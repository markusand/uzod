"""Type stubs for uzod schema validator"""

# pylint: disable=unused-argument, redefined-builtin, missing-docstring, super-init-not-called

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Tuple,
    TypeVar,
    Self,
)

Check = Callable[[Any], bool]

T = TypeVar("T")
U = TypeVar("U")

class ValidationError(Exception):
    """Validation error"""

class Validator(Generic[T]):
    """Base validator"""

    _optional: bool
    _nullable: bool
    _default: Any
    _checks: List[Tuple[Check, str]]

    def __init__(self) -> None: ...
    @property
    def optional(self) -> Self: ...
    @property
    def nullable(self) -> Self: ...
    def default(self, val: T) -> Self: ...
    def refine(self, fn: Check, msg: str = "invalid") -> Self: ...
    def _run_checks(self, val: T) -> T: ...
    def parse(self, val: Any) -> T: ...
    def clone(self) -> Self: ...
    def _parse(self, val: Any) -> T: ...

class String(Validator[str]):
    """String validator"""

    def __init__(self, *, min: int | None = None, max: int | None = None) -> None: ...
    def min(self, length: int, msg: str | None = None) -> Self: ...
    def max(self, length: int, msg: str | None = None) -> Self: ...
    def _parse(self, val: Any) -> str: ...

class Integer(Validator[int]):
    """Integer validator"""

    def __init__(self, *, min: int | None = None, max: int | None = None) -> None: ...
    def min(self, value: int, msg: str | None = None) -> Self: ...
    def max(self, value: int, msg: str | None = None) -> Self: ...
    def _parse(self, val: Any) -> int: ...

class Float(Validator[float]):
    """Float validator"""

    def __init__(self, *, min: float | None = None, max: float | None = None) -> None: ...
    def min(self, value: float, msg: str | None = None) -> Self: ...
    def max(self, value: float, msg: str | None = None) -> Self: ...
    def _parse(self, val: Any) -> float: ...

class Boolean(Validator[bool]):
    """Boolean validator"""

    def _parse(self, val: Any) -> bool: ...

class Literal(Validator[Any]):
    """Literal validator"""

    def __init__(self, *values: Any) -> None: ...

    _values: Tuple[Any, ...]

    def _parse(self, val: Any) -> Any: ...

class Array(Validator[List[U]]):
    """Array validator"""

    _shape: Validator[U]

    def __init__(
        self, shape: Validator[U], *, min: int | None = None, max: int | None = None
    ) -> None: ...
    def min(self, length: int, msg: str | None = None) -> Self: ...
    def max(self, length: int, msg: str | None = None) -> Self: ...
    def _parse(self, val: Any) -> List[U]: ...

class Object(Validator[Dict[str, Any]]):
    """Object validator"""

    _shape: Dict[str, Validator[Any]]
    _strict: bool

    def __init__(self, shape: Dict[str, Validator[Any]], *, strict: bool = False) -> None: ...
    @property
    def strict(self) -> Self: ...
    @property
    def shape(self) -> Dict[str, Any]: ...
    def extend(self, shape: Dict[str, Validator[Any]]) -> "Object": ...
    def partial(self, keys: List[str] | None = None) -> "Object": ...
    def _parse(self, val: Any) -> Dict[str, Any]: ...

K = TypeVar("K")
V = TypeVar("V")

class Record(Validator[Dict[K, V]]):
    """Record validator"""

    _key: Validator[K]
    _value: Validator[V]

    def __init__(self, key: Validator[K], value: Validator[V]) -> None: ...
    def _parse(self, val: Any) -> Dict[K, V]: ...

class Number(Float):
    """Number validator that preserves int vs float"""

    def _parse(self, val: Any) -> int | float: ...

class Union(Validator[Any]):
    """Or validator"""

    _schemas: List[Validator[Any]]

    def __init__(self, *schemas: Validator[Any]) -> None: ...
    def _parse(self, val: Any) -> Any: ...

class z:  # pylint: disable=invalid-name
    """Shortcuts for common validators"""

    string: type[String]
    integer: type[Integer]
    float: type[Float]
    number: type[Number]
    boolean: type[Boolean]
    literal: type[Literal]
    array: type[Array]
    object: type[Object]
    record: type[Record]
    union: type[Union]
