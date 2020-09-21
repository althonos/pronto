"""Object hierarchy of property-value annotations in OBO files.
"""

import functools

import fastobo

from .utils.meta import roundrepr, typechecked


__all__ = ["PropertyValue", "LiteralPropertyValue", "ResourcePropertyValue"]


class PropertyValue(object):
    """A property-value, which adds annotations to an entity."""

    property: str
    __slots__ = ("__weakref__", "property")


@roundrepr
@functools.total_ordering
class LiteralPropertyValue(PropertyValue):
    """A property-value which adds a literal annotation to an entity."""

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
        if not fastobo.id.is_valid(property):
            raise ValueError("invalid identifier: {}".format(property))
        if not fastobo.id.is_valid(datatype):
            raise ValueError("invalid identifier: {}".format(datatype))

        self.property = property
        self.literal = literal
        self.datatype = datatype

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LiteralPropertyValue):
            return (
                self.property == other.property
                and self.literal == other.literal
                and self.datatype == other.datatype
            )
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, LiteralPropertyValue):
            return (self.property, self.literal, self.datatype) < (
                other.property,
                other.literal,
                other.datatype,
            )
        elif isinstance(other, ResourcePropertyValue):
            return self.property < other.property
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash((LiteralPropertyValue, self.property, self.literal, self.datatype))


@roundrepr
@functools.total_ordering
class ResourcePropertyValue(PropertyValue):
    """A property-value which adds a resource annotation to an entity."""

    resource: str
    __slots__ = ("resource",)

    @typechecked()
    def __init__(self, property: str, resource: str):
        """Create a new `ResourcePropertyValue` instance.

        Arguments:
            property (str): The annotation property, as an OBO identifier.
            resource (str): The annotation entity value, as an OBO identifier.

        """
        if not fastobo.id.is_valid(property):
            raise ValueError("invalid identifier: {}".format(property))
        if not fastobo.id.is_valid(resource):
            raise ValueError("invalid identifier: {}".format(resource))

        self.property = property
        self.resource = resource

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ResourcePropertyValue):
            return (self.property, self.resource) == (other.property, other.resource)
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, ResourcePropertyValue):
            return (self.property, self.resource) < (other.property, other.resource)
        elif isinstance(other, LiteralPropertyValue):
            return self.property < other.property
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash((LiteralPropertyValue, self.property, self.resource))
