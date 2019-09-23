try:
    if __debug__:
        from nanoset import NanoSet as set
    else:
        from nanoset import PicoSet as set
except ImportError:
    from builtins import set
