"""Warnings raised by the library.
"""


class ProntoWarning(Warning):
    """The class for all warnings raised by `pronto`."""

    pass


class NotImplementedWarning(ProntoWarning, NotImplementedError):
    """Some part of the code is yet to be implemented."""

    pass


class UnstableWarning(ProntoWarning):
    """The behaviour of the executed code might change in the future."""

    pass


class SyntaxWarning(ProntoWarning, SyntaxError):
    """The parsed document contains incomplete or unsound constructs."""

    def __init__(self, *args, **kwargs):
        ProntoWarning.__init__(self, *args, **kwargs)
        SyntaxError.__init__(self, *args, **kwargs)
