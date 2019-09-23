import bz2
import io
import gzip
import lzma
import typing
from typing import BinaryIO, Optional

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

def decompress(reader: BinaryIO, path: str=None) -> BinaryIO:
    """Given a binary file-handle, decompress it if it is compressed.
    """

    buffered = BufferedReader(reader)

    # TODO: more compression algorithms
    if buffered.peek().startswith(MAGIC_GZIP):
        return gzip.GzipFile(mode="rb", fileobj=buffered)
    elif buffered.peek().startswith(MAGIC_LZMA):
        return lzma.LZMAFile(buffered, mode="rb")
    elif buffered.peek().startswith(MAGIC_BZIP2):
        return bz2.BZ2File(buffered, mode="rb")
    else:
        return buffered
