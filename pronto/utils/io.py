import bz2
import codecs
import gzip
import io
import lzma
import typing
import urllib.request
import warnings
from http.client import HTTPResponse
from typing import BinaryIO, ByteString, Dict, Optional, Union, cast

import chardet

MAGIC_GZIP = bytearray([0x1F, 0x8B])
MAGIC_LZMA = bytearray([0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00, 0x00])
MAGIC_BZIP2 = bytearray([0x42, 0x5A, 0x68])


class BufferedReader(io.BufferedReader):
    """A patch for `io.BufferedReader` supporting `http.client.HTTPResponse`."""

    def read(self, size: Optional[int] = -1) -> bytes:
        try:
            return super(BufferedReader, self).read(size)
        except ValueError:
            if typing.cast(io.BufferedReader, self.closed):
                return b""
            raise


class EncodedFile(codecs.StreamRecoder):
    def __init__(
        self,
        file: BinaryIO,
        data_encoding: str,
        file_encoding: Optional[str] = None,
        errors: str = "strict",
    ):
        if file_encoding is None:
            file_encoding = data_encoding
        data_info = codecs.lookup(data_encoding)
        file_info = codecs.lookup(file_encoding)
        super().__init__(
            file,
            data_info.encode,
            data_info.decode,
            file_info.streamreader,
            file_info.streamwriter,
            errors,
        )
        # Add attributes to simplify introspection
        self.data_encoding = data_encoding
        self.file_encoding = file_encoding

    def read(self, size: Optional[int] = -1) -> bytes:
        chunk = super().read(-1 if size is None else size)
        return chunk.replace(b"\r\n", b"\n")

    def readinto(self, buffer: ByteString) -> int:
        chunk = self.read(len(buffer) // 2)
        typing.cast(bytearray, buffer)[: len(chunk)] = chunk
        return len(chunk)


def get_handle(path: str, timeout: int = 2) -> BinaryIO:
    """Given a path or URL, get a binary handle for that path."""
    try:
        return open(path, "rb", buffering=0)
    except Exception as err:
        headers = {"Keep-Alive": f"timeout={timeout}"}
        request = urllib.request.Request(path, headers=headers)
        res: HTTPResponse = urllib.request.urlopen(request, timeout=timeout)
        if not res.status == 200:
            raise ValueError(f"could not open {path}: {res.status} ({res.msg})")
        if res.headers.get("Content-Encoding") in {"gzip", "deflate"}:
            f = gzip.GzipFile(filename=res.geturl(), mode="rb", fileobj=res)
            return typing.cast(BinaryIO, f)
        return res


def get_location(reader: BinaryIO) -> Optional[str]:
    """Given a binary file-handle, try to extract the path/URL to the file."""
    return (
        getattr(reader, "name", None)
        or getattr(reader, "url", None)
        or getattr(reader, "geturl", lambda: None)()
    )


def decompress(
    reader: io.RawIOBase, path: Optional[str] = None, encoding: Optional[str] = None
) -> BinaryIO:
    """Given a binary file-handle, decompress it if it is compressed."""
    buffered = BufferedReader(reader)

    # Decompress the stream if it is compressed
    if buffered.peek().startswith(MAGIC_GZIP):
        decompressed = BufferedReader(
            typing.cast(
                io.RawIOBase,
                gzip.GzipFile(mode="rb", fileobj=typing.cast(BinaryIO, buffered)),
            )
        )
    elif buffered.peek().startswith(MAGIC_LZMA):
        decompressed = BufferedReader(
            typing.cast(
                io.RawIOBase, lzma.LZMAFile(typing.cast(BinaryIO, buffered), mode="rb")
            )
        )
    elif buffered.peek().startswith(MAGIC_BZIP2):
        decompressed = BufferedReader(
            typing.cast(
                io.RawIOBase, bz2.BZ2File(typing.cast(BinaryIO, buffered), mode="rb")
            )
        )
    else:
        decompressed = buffered

    # Attempt to detect the encoding and decode the stream
    det: Dict[str, Union[str, float]] = chardet.detect(decompressed.peek())
    confidence = 1.0 if encoding is not None else cast(float, det["confidence"])
    encoding = encoding if encoding is not None else cast(str, det["encoding"])

    if encoding == "ascii":
        encoding = "utf-8"
    if confidence < 1.0:
        warnings.warn(
            f"unsound encoding, assuming {encoding} ({confidence:.0%} confidence)",
            UnicodeWarning,
            stacklevel=3,
        )

    if encoding == "utf-8":
        return typing.cast(BinaryIO, decompressed)
    else:
        return typing.cast(
            BinaryIO,
            BufferedReader(
                typing.cast(
                    io.RawIOBase,
                    EncodedFile(
                        typing.cast(typing.BinaryIO, decompressed),
                        "UTF-8",
                        typing.cast(str, det["encoding"]),
                    ),
                )
            ),
        )
