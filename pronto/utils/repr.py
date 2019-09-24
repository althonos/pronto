import inspect
import collections


def roundrepr(cls):
    """A class-decorator to build a minimal `__repr__` method that roundtrips.
    """

    # Extract signature of `__init__`
    spec = inspect.getfullargspec(cls.__init__)
    if spec.varargs is not None or spec.varkw is not None:
        raise TypeError("cannot use `roundrepr` on a class with variadic `__init__`")

    # Separate positional and default arguments
    d = len(spec.defaults) if spec.defaults is not None else 0
    if d != 0:
        mandatory = spec.args[1:-d]
        optional = [(k, v) for (k, v) in zip(spec.args[-d:], spec.defaults or ())]
    else:
        mandatory = spec.args[1:]
        optional = []

    # Derive the __repr__ implementation
    def __repr__(self):
        args = [getattr(self, x) for x in mandatory]
        kwargs = {attr:(getattr(self, attr), default) for (attr, default) in optional}
        return make_repr(cls.__name__, *args, **kwargs)

    # Hotpatch the class and return it
    cls.__repr__ = __repr__
    return cls


def make_repr(class_name, *args, **kwargs):
    # type: (Text, *object, **Tuple[object, object]) -> Text
    """Generate a repr string.

    Positional arguments should be the positional arguments used to
    construct the class. Keyword arguments should consist of tuples of
    the attribute value and default. If the value is the default, then
    it won't be rendered in the output.

    Example:
        >>> class MyClass(object):
        ...     def __init__(self, name=None):
        ...         self.name = name
        ...     def __repr__(self):
        ...         return make_repr('MyClass', 'foo', name=(self.name, None))
        >>> MyClass('Will')
        MyClass('foo', name='Will')
        >>> MyClass(None)
        MyClass()

    Credits:
        `PyFilesystem2 <https://github.com/PyFilesystem/pyfilesystem2/blob/master/fs/_repr.py>`_
        code developed by `Will McGugan <https://github.com/willmcgugan>`_.
    """
    arguments = [repr(arg) for arg in args]
    arguments.extend(
        [
            "{}={!r}".format(name, value)
            for name, (value, default) in sorted(kwargs.items())
            if value != default and value
        ]
    )
    return "{}({})".format(class_name, ", ".join(arguments))
