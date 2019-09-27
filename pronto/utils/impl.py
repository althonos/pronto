try:
    if __debug__:
        from nanoset import NanoSet as set
    else:
        from nanoset import PicoSet as set
except ImportError:
    from builtins import set

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree
