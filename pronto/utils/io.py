import bz2
import codecs
import io
import gzip
import lzma
import typing
from typing import BinaryIO, Optional

import chardet
import requests


MAGIC_GZIP = bytearray([0x1F, 0x8B])
MAGIC_LZMA = bytearray([0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00, 0x00])
MAGIC_BZIP2 = bytearray([0x42, 0x5A, 0x68])


class BufferedReader(io.BufferedReader):
    """A patch for `io.BufferedReader` supporting `http.client.HTTPResponse`.
    """

    def read(self, size=-1):
        try:
            return super(BufferedReader, self).read(size)
        except ValueError:
            return b''


class EncodedFile(codecs.StreamRecoder):

    def __init__(self, file, data_encoding, file_encoding=None, errors='strict'):
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
            errors
        )
        # Add attributes to simplify introspection
        self.data_encoding = data_encoding
        self.file_encoding = file_encoding

    def read(self, size=-1):
        chunk = super().read(size)
        return chunk.replace(b'\r\n', b'\n')

    def readinto(self, buffer):
        chunk = self.read(len(buffer))
        buffer[:len(chunk)] = chunk
        return len(chunk)




def get_handle(path: str, session: requests.Session, timeout: int=2) -> BinaryIO:
    """Given a path or URL, get a binary handle for that path.
    """
    try:
        return open(path, "rb", buffering=0)
    except Exception as err:
        headers = {'Keep-Alive': f'timeout={timeout}'}
        res = session.get(path, stream=True, headers=headers)
        if not res.raw.status == 200:
            raise ValueError("could not open {}: {}", res.reason) from err
        if res.raw.headers.get('Content-Encoding') in {'gzip', 'deflate'}:
            return gzip.GzipFile(filename=res.url, mode="rb", fileobj=res.raw)
        return res.raw

def get_location(reader: BinaryIO) -> Optional[str]:
    """Given a binary file-handle, try to extract the path/URL to the file.
    """
    return (
        getattr(reader, "name", None)
        or getattr(reader, "url", None)
        or getattr(reader, 'geturl', lambda: None)()
    )

def decompress(
        reader: io.BufferedReader,
        path: Optional[str] = None,
        encoding: Optional[str] = None
) -> BinaryIO:
    """Given a binary file-handle, decompress it if it is compressed.
    """

    buffered = BufferedReader(reader)

    # Decompress the stream if it is compressed
    if buffered.peek().startswith(MAGIC_GZIP):
        decompressed = BufferedReader(gzip.GzipFile(mode="rb", fileobj=buffered))
    elif buffered.peek().startswith(MAGIC_LZMA):
        decompressed = BufferedReader(lzma.LZMAFile(buffered, mode="rb"))
    elif buffered.peek().startswith(MAGIC_BZIP2):
        decompressed = BufferedReader(bz2.BZ2File(buffered, mode="rb"))
    else:
        decompressed = buffered

    # Attempt to detect the encoding and decode the stream
    if encoding is not None:
        det = dict(encoding=encoding, confidence=1.0)
    else:
        det = chardet.detect(decompressed.peek())
    if det['confidence'] == 1.0:
        return BufferedReader(EncodedFile(decompressed, 'UTF-8', det['encoding']))
    else:
        warnings.warn('could not find encoding, assuming UTF-8')
        return decompressed
