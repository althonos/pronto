"""Object hierarchy of property-value annotations in OBO files.
"""

import fastobo

from .utils.impl import set
from .utils.meta import roundrepr, typechecked


class PropertyValue(object):
    """A property-value, which adds annotations to an entity.
    """

    property: str
    __slots__ = ("__weakref__", "property")

    @classmethod
    def _from_ast(cls, pv: fastobo.pv.AbstractPropertyValue) -> 'PropertyValue':
        if isinstance(pv, fastobo.pv.LiteralPropertyValue):
            return LiteralPropertyValue._from_ast(pv)
        elif isinstance(pv, fastobo.pv.ResourcePropertyValue):
            return ResourcePropertyValue._from_ast(pv)
        else:
            msg = "'pv' must be AbstractPropertyValue, not {}"
            raise TypeError(msg.format(type(pv).__name__))


@roundrepr
class LiteralPropertyValue(PropertyValue):
    """A property-value which adds a literal annotation to an entity.
    """

    literal: str
    datatype: str
    __slots__ = ("literal", "datatype")

    @typechecked()
    def __init__(self, property: str, literal: str, datatype: str = "xsd:string"):
        """Create a new `LiteralPropertyValue` instance.

        Arguments:
            property (str): The annotation property, as an OBO identifier.
            literal (str): The serialized value of the annotation.
            datatype (str): The datatype of the annotation property value.
                Defaults to `xsd:string`.

        """
        self.property = str(fastobo.id.parse(property))
        self.literal = literal
        self.datatype = str(fastobo.id.parse(datatype))

    @classmethod
    def _from_ast(cls, pv: fastobo.pv.LiteralPropertyValue) -> 'LiteralPropertyValue':
        return cls(str(pv.relation), pv.value, str(pv.datatype))


@roundrepr
class ResourcePropertyValue(PropertyValue):
    """A property-value which adds a resource annotation to an entity.
    """

    resource: str
    __slots__ = ("resource",)

    @typechecked()
    def __init__(self, property: str, resource: str):
        """Create a new `ResourcePropertyValue` instance.

        Arguments:
            property (str): The annotation property, as an OBO identifier.
            resource (str): The annotation entity value, as an OBO identifier.

        """
        self.property = str(fastobo.id.parse(property))
        self.resource = str(fastobo.id.parse(resource))

    @classmethod
    def _from_ast(cls, pv: fastobo.pv.ResourcePropertyValue) -> 'ResourcePropertyValue':
        return cls(str(pv.relation), str(pv.value))
