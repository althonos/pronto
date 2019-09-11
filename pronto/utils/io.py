import io
import gzip
import typing
from typing import BinaryIO, Optional

import requests


MAGIC_GZIP = b'\x1f\x8b'


def get_handle(path: str, session: requests.Session) -> BinaryIO:
    """Given a path or URL, get a binary handle for that path.
    """
    try:
        return open(path, "rb", buffering=0)
    except Exception as err:
        res = session.get(path, stream=True)
        if not res.ok:
            raise ValueError("could not open {}: {}", res.reason) from err
        return io.BytesIO(res.content) if res.raw.closed else res.raw

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

    buffered = io.BufferedReader(reader)

    # TODO: more compression algorithms
    if buffered.peek(2) == MAGIC_GZIP:
        return gzip.GzipFile(mode="rb", fileobj=buffered)
    else:
        return buffered
