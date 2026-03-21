"""Schema validator"""

_MISSING = object()


class ValidationError(Exception):
    """Validation error"""


class Validator:
    """Base validator"""

    def __init__(self):
        self._optional = False
        self._nullable = False
        self._default = _MISSING
        self._checks = []

    @property
    def optional(self):
        """Mark field as optional"""
        self._optional = True
        return self

    @property
    def nullable(self):
        """Mark field as nullable"""
        self._nullable = True
        return self

    def default(self, val):
        """Set default value for optional field"""
        self._default = val
        self._optional = True
        return self

    def refine(self, fn, msg="invalid"):
        """Add refinement check"""
        self._checks.append((fn, msg))
        return self

    def _run_checks(self, val):
        for fn, msg in self._checks:
            if not fn(val):
                raise ValidationError(msg)
        return val

    def parse(self, val):
        """Parse and validate value"""
        if val is _MISSING:
            if self._default is not _MISSING:
                return self._default
            if self._optional:
                return None
            raise ValidationError("required")

        if val is None:
            if self._default is not _MISSING:
                return self._default
            if self._nullable:
                return None
            raise ValidationError("required")

        return self._parse(val)

    def _parse(self, val):
        raise NotImplementedError


class String(Validator):
    """String validator"""

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, length, msg=None):
        """Set minimum length"""
        return self.refine(lambda v: len(v) >= length, msg or f"too short, at least {length} chars")

    def max(self, length, msg=None):
        """Set maximum length"""
        return self.refine(lambda v: len(v) <= length, msg or f"too long, at most {length} chars")

    def _parse(self, val):
        if not isinstance(val, str):
            raise ValidationError(f"expected str, got {type(val).__name__}")
        return self._run_checks(val)


class Integer(Validator):
    """Integer validator"""

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, value, msg=None):
        """Set minimum value"""
        return self.refine(lambda v: v >= value, msg or f"too small, at least {value}")

    def max(self, value, msg=None):
        """Set maximum value"""
        return self.refine(lambda v: v <= value, msg or f"too large, at most {value}")

    def _parse(self, val):
        """Parse and validate value"""
        if not isinstance(val, int) or isinstance(val, bool):
            raise ValidationError(f"expected int, got {type(val).__name__}")
        return self._run_checks(val)


class Float(Validator):
    """Float validator"""

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, value, msg=None):
        """Set minimum value"""
        return self.refine(lambda v: v >= value, msg or f"too small, at least {value}")

    def max(self, value, msg=None):
        """Set maximum value"""
        return self.refine(lambda v: v <= value, msg or f"too large, at most {value}")

    def _parse(self, val):
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValidationError(f"expected float, got {type(val).__name__}")
        return self._run_checks(float(val))


class Boolean(Validator):
    """Boolean validator"""

    def _parse(self, val):
        if not isinstance(val, bool):
            raise ValidationError(f"expected bool, got {type(val).__name__}")
        return self._run_checks(val)


class Literal(Validator):
    """Literal validator"""

    def __init__(self, *values):
        super().__init__()
        self._values = values

    def _parse(self, val):
        if val not in self._values:
            raise ValidationError(f"expected one of ({', '.join(self._values)}), got {val}")
        return val


class Array(Validator):
    """Array validator"""

    def __init__(self, shape, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        self._shape = shape
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, length, msg=None):
        """Set minimum length"""
        return self.refine(lambda v: len(v) >= length, msg or f"too few items, at least {length}")

    def max(self, length, msg=None):
        """Set maximum length"""
        return self.refine(lambda v: len(v) <= length, msg or f"too many items, at most {length}")

    def _parse(self, val):
        if not isinstance(val, (list, tuple)):
            raise ValidationError(f"expected list, got {type(val).__name__}")
        out = []
        for i, item in enumerate(val):
            try:
                out.append(self._shape.parse(item))
            except ValidationError as error:
                raise ValidationError(f"[{i}] {error}") from error
        self._run_checks(out)
        return out


class Object(Validator):
    """Object validator"""

    def __init__(self, shape, *, strict=False):
        super().__init__()
        self._shape = shape
        self._strict = strict

    def strict(self):
        """Reject unknown keys"""
        self._strict = True
        return self

    def _parse(self, val):
        if not isinstance(val, dict):
            raise ValidationError(f"expected dict, got {type(val).__name__}")

        # Check for unknown keys in strict mode
        if self._strict:
            extra = set(val.keys()) - set(self._shape.keys())
            if extra:
                raise ValidationError(f"unexpected keys: {', '.join(extra)}")

        out = {}
        for key, schema in self._shape.items():
            try:
                out[key] = schema.parse(val.get(key, _MISSING))
            except ValidationError as error:
                raise ValidationError(f"{key}: {error}") from error
        return self._run_checks(out)


class Union(Validator):
    """Or validator"""

    def __init__(self, *schemas):
        super().__init__()
        self._schemas = list(schemas)

    def _parse(self, val):
        errors = []
        for schema in self._schemas:
            try:
                return schema.parse(val)
            except ValidationError as error:
                errors.append(str(error))
        raise ValidationError("no variant matched:\n" + "\n".join(f"  - {e}" for e in errors))


class z:  # pylint: disable=invalid-name
    """Shortcuts for common validators"""

    string = String
    integer = Integer
    float = Float
    number = Float
    boolean = Boolean
    literal = Literal
    array = Array
    object = Object
    union = Union
