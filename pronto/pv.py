import fastobo

from .utils.repr import roundrepr
from .utils.set import set


class PropertyValue(object):
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
    property: str
    literal: str
    datatype: str

    __slots__ = ("literal", "datatype")

    def __init__(self, property: str, literal: str, datatype: str = "xsd:string"):
        self.property = str(fastobo.id.parse(property))
        self.literal = literal
        self.datatype = str(fastobo.id.parse(datatype))

    @classmethod
    def _from_ast(cls, pv: fastobo.pv.LiteralPropertyValue) -> 'LiteralPropertyValue':
        return cls(str(pv.relation), pv.value, str(pv.datatype))


@roundrepr
class ResourcePropertyValue(PropertyValue):
    property: str
    resource: str

    __slots__ = ("resource",)

    def __init__(self, property: str, resource: str):
        self.property = str(fastobo.id.parse(property))
        self.resource = str(fastobo.id.parse(resource))

    @classmethod
    def _from_ast(cls, pv: fastobo.pv.ResourcePropertyValue) -> 'ResourcePropertyValue':
        return cls(str(pv.relation), str(pv.value))
