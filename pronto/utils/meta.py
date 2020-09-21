import collections
import contextlib
import functools
import inspect
import itertools
import sys
import typing
from typing import Callable, ClassVar, Iterator, List, Optional, Tuple, Type

T = typing.TypeVar("T")
F = typing.TypeVar("F", bound=Callable[..., object])


class typechecked(object):

    _disable = False

    if sys.version_info >= (3, 7):
        Set = set
        FrozenSet = frozenset
    else:
        Set = typing.Set
        FrozenSet = typing.FrozenSet

    @classmethod
    @typing.no_type_check
    def check_type(cls, hint: object, value: object) -> Tuple[bool, str]:
        # None: check if None
        if hint is None.__class__:
            return (value is None, "None")
        # typing.Any is always true
        if typing.cast(str, getattr(hint, "_name", None)) == "typing.Any":
            return (True, "any object")
        # typing.Set needs to check member types
        if typing.cast(object, getattr(hint, "__origin__", None)) is cls.Set:
            if not isinstance(value, collections.abc.MutableSet):
                return (False, f"set of { hint.__args__ }")
            for arg in value:
                well_typed, type_name = cls.check_type(hint.__args__[0], arg)
                if not well_typed:
                    return (False, f"set of { type_name }")
            return (True, f"set of { hint.__args__ }")
        # typing.FrozenSet needs to check member types
        if typing.cast(object, getattr(hint, "__origin__", None)) is cls.FrozenSet:
            if not isinstance(value, collections.abc.Set):
                return (False, f"frozen set of { hint.__args__ }")
            for arg in value:
                well_typed, type_name = cls.check_type(hint.__args__[0], arg)
                if not well_typed:
                    return (False, f"frozenset of { type_name }")
            return (True, f"frozenset of { hint.__args__[0] }")
        # typing.Union needs to be a valid type
        if getattr(hint, "__origin__", None) is typing.Union:
            results = {}
            for arg in hint.__args__:
                results[arg] = cls.check_type(arg, value)
            ok = any(ok for ok, name in results.values())
            return (ok, ", ".join(name for ok, name in results.values()))
        # direct type annotation: simply do an instance check
        if isinstance(hint, type):
            return (isinstance(value, hint), hint.__name__)
        return (False, "<unknown>")

    @classmethod
    @contextlib.contextmanager
    def disabled(cls) -> Iterator[None]:
        initial_state = cls._disable
        try:
            # cls._disable = True
            yield
        finally:
            cls._disable = initial_state

    def __init__(self, property: bool = False) -> None:
        self.property = property

    def __call__(self, func: F) -> F:
        if not __debug__:
            return func

        hints = typing.get_type_hints(func)
        signature = inspect.signature(func)

        @functools.wraps(func)
        def newfunc(*args, **kwargs):
            if not self._disable:
                callargs = signature.bind(*args, **kwargs).arguments
                for name, value in callargs.items():
                    if name in hints:
                        well_typed, type_name = self.check_type(hints[name], value)
                        if not well_typed:
                            msg = f"'{{}}' must be {type_name}, not {type(value).__name__}"
                            if self.property:
                                raise TypeError(msg.format(func.__name__))
                            else:
                                raise TypeError(msg.format(name))
            return func(*args, **kwargs)

        return newfunc  # type: ignore


class roundrepr(object):
    """A class-decorator to build a minimal `__repr__` method that roundtrips."""

    @staticmethod
    def make(class_name: str, *args: object, **kwargs: Tuple[object, object]) -> str:
        """Generate a repr string.

        Positional arguments should be the positional arguments used to
        construct the class. Keyword arguments should consist of tuples of
        the attribute value and default. If the value is the default, then
        it won't be rendered in the output.

        Example:
            >>> from pronto.utils.meta import roundrepr
            >>> class MyClass(object):
            ...     def __init__(self, name=None):
            ...         self.name = name
            ...     def __repr__(self):
            ...         return roundrepr.make('MyClass', 'foo', name=(self.name, None))
            >>> MyClass('Will')
            MyClass('foo', name='Will')
            >>> MyClass(None)
            MyClass('foo')

        Note:
            This functions uses code developed by `Will McGugan <https://github.com/willmcgugan>`_
            for `PyFilesystem2 <https://github.com/PyFilesystem/pyfilesystem2/blob/master/fs/_repr.py>`_

        """
        arguments: List[str] = [repr(arg) for arg in args]
        arguments.extend(
            [
                "{}={!r}".format(name, value)
                for name, (value, default) in sorted(kwargs.items())
                if value != default and value
            ]
        )
        return "{}({})".format(class_name, ", ".join(arguments))

    def __new__(self, cls: Type[T]) -> T:  # type: ignore
        obj = super().__new__(self)
        obj.__init__()
        if isinstance(cls, type):
            return obj(cls)
        return obj

    def __call__(self, cls: T) -> T:

        # Extract signature of `__init__`
        sig = inspect.signature(cls.__init__)  # type: ignore
        if not all(p.kind is p.POSITIONAL_OR_KEYWORD for p in sig.parameters.values()):
            raise TypeError(
                "cannot use `roundrepr` on a class with variadic `__init__`"
            )

        # Derive the __repr__ implementation
        def __repr__(self_):
            """Return a `repr` string that roundtrips. Computed by @roundrepr."""
            args, kwargs = [], {}
            for name, param in itertools.islice(sig.parameters.items(), 1, None):
                if param.default is inspect.Parameter.empty:
                    args.append(getattr(self_, name))
                else:
                    kwargs[name] = (getattr(self_, name), param.default)
            return self.make(cls.__name__, *args, **kwargs)

        # Hotpatch the class and return it
        cls.__repr__ = __repr__  # type: ignore
        return cls
