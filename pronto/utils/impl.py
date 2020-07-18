try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree  # type: ignore
