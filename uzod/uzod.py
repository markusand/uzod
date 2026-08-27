"""
uzod - Lightweight validation library for (Micro)Python.

This module provides runtime type checking and validation with a clean,
chainable API inspired by Zod. It's designed to be lightweight with zero
dependencies, making it perfect for MicroPython projects and embedded systems.
"""

# pylint: disable=protected-access

_MISSING = object()


class ValidationError(Exception):
    """
    Exception raised when validation fails.
    """


class Validator:
    """
    Base validator class providing common validation modifiers.

    All specific validators (String, Integer, etc.) inherit from this class
    and gain access to common modifiers like optional, nullable, default,
    and refine. This class also handles the core parsing logic.

    Attributes:
        _optional: Whether the field can be omitted (returns None if missing).
        _nullable: Whether the field can explicitly be None.
        _default: Default value to use when field is missing or None.
        _checks: List of custom refinement functions to apply.
    """

    def __init__(self):
        self._optional = False
        self._nullable = False
        self._default = _MISSING
        self._checks = []

    @property
    def optional(self):
        """
        Mark field as optional.

        When a field is optional, it can be omitted from the input.
        If omitted, the parsed value will be None (unless a default is set).

        Returns:
            Self for method chaining.
        """
        self._optional = True
        return self

    @property
    def nullable(self):
        """
        Mark field as nullable.

        When a field is nullable, it can explicitly be None.
        A None value will pass validation and return None.

        Returns:
            Self for method chaining.
        """
        self._nullable = True
        return self

    def default(self, val):
        """
        Set default value for optional field.

        Provides a default value to use when the field is missing or None.
        Automatically marks the field as optional.

        Args:
            val: The default value to use.

        Returns:
            Self for method chaining.
        """
        self._default = val
        self._optional = True
        return self

    def refine(self, fn, msg="invalid"):
        """
        Add custom validation refinement.

        Allows adding custom validation logic beyond basic type checking.
        The function should return True if validation passes, False otherwise.

        Args:
            fn: A callable that takes the value and returns bool.
            msg: Error message to show if validation fails. Defaults to "invalid".

        Returns:
            Self for method chaining.
        """
        self._checks.append((fn, msg))
        return self

    def _run_checks(self, val):
        for fn, msg in self._checks:
            if not fn(val):
                raise ValidationError(msg)
        return val

    def parse(self, val):
        """
        Parse and validate a value against the schema.

        This is the main entry point for validation. It handles optional/nullable
        logic, default values, and delegates to the specific validator's _parse method.

        Args:
            val: The value to validate.

        Returns:
            The validated value (possibly transformed or defaulted).

        Raises:
            ValidationError: If validation fails.
        """
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

    def clone(self):
        """
        Create an independent copy of this validator.

        Returns a new instance with the same type, modifiers, and refinements,
        but independent from the original — changes to one won't affect the other.

        Returns:
            A new validator instance of the same type.
        """
        new = object.__new__(self.__class__)
        new._optional = self._optional
        new._nullable = self._nullable
        new._default = self._default
        new._checks = list(self._checks)
        return new

    def _parse(self, val):
        raise NotImplementedError


class String(Validator):
    """
    Validator for string values.

    Validates that a value is a string and optionally enforces
    length constraints through min/max parameters or methods.
    """

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, length, msg=None):
        """
        Set minimum string length constraint.

        Args:
            length: Minimum number of characters required.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: len(v) >= length, msg or f"too short, at least {length} chars")

    def max(self, length, msg=None):
        """
        Set maximum string length constraint.

        Args:
            length: Maximum number of characters allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: len(v) <= length, msg or f"too long, at most {length} chars")

    def _parse(self, val):
        if not isinstance(val, str):
            raise ValidationError(f"expected str, got {type(val).__name__}")
        return self._run_checks(val)


class Integer(Validator):
    """
    Validator for integer values.

    Validates that a value is an integer (excluding booleans) and optionally
    enforces range constraints through min/max parameters or methods.
    """

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, value, msg=None):
        """
        Set minimum integer value constraint.

        Args:
            value: Minimum value allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: v >= value, msg or f"too small, at least {value}")

    def max(self, value, msg=None):
        """
        Set maximum integer value constraint.

        Args:
            value: Maximum value allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: v <= value, msg or f"too large, at most {value}")

    def _parse(self, val):
        """
        Internal parse method for integer validation.

        Args:
            val: The value to validate.

        Returns:
            The validated integer value.

        Raises:
            ValidationError: If value is not an integer.
        """
        if not isinstance(val, int) or isinstance(val, bool):
            raise ValidationError(f"expected int, got {type(val).__name__}")
        return self._run_checks(val)


class Float(Validator):
    """
    Validator for float/numeric values.

    Validates that a value is a float or integer (excluding booleans) and
    optionally enforces range constraints through min/max parameters or methods.
    Integer values are automatically converted to float.
    """

    def __init__(self, *, min=None, max=None):  # pylint: disable=redefined-builtin
        super().__init__()
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, value, msg=None):
        """
        Set minimum numeric value constraint.

        Args:
            value: Minimum value allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: v >= value, msg or f"too small, at least {value}")

    def max(self, value, msg=None):
        """
        Set maximum numeric value constraint.

        Args:
            value: Maximum value allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: v <= value, msg or f"too large, at most {value}")

    def _parse(self, val):
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValidationError(f"expected float, got {type(val).__name__}")
        return self._run_checks(float(val))


class Boolean(Validator):
    """
    Validator for boolean values.

    Validates that a value is a boolean (True or False).
    No additional constraints or modifiers are available.
    """

    def _parse(self, val):
        if not isinstance(val, bool):
            raise ValidationError(f"expected bool, got {type(val).__name__}")
        return self._run_checks(val)


class Literal(Validator):
    """
    Validator for literal/enum values.

    Validates that a value exactly matches one of the allowed literal values.
    Useful for enums, constants, and restricting to specific options.
    """

    def __init__(self, *values):
        """
        Initialize literal validator with allowed values.

        Args:
            *values: One or more allowed literal values.
        """
        super().__init__()
        self._values = values

    def clone(self):
        new = super().clone()
        new._values = self._values
        return new

    def _parse(self, val):
        if val not in self._values:
            raise ValidationError(f"expected one of ({', '.join(self._values)}), got {val}")
        return val


class Array(Validator):
    """
    Validator for array/list values.

    Validates that a value is a list or tuple and that all elements
    match the specified schema. Optionally enforces length constraints.
    """

    def __init__(self, shape, *, min=None, max=None):  # pylint: disable=redefined-builtin
        """
        Initialize array validator with element schema.

        Args:
            shape: The validator schema for array elements.
            min: Optional minimum array length.
            max: Optional maximum array length.
        """
        super().__init__()
        self._shape = shape
        if min is not None:
            self.min(min)
        if max is not None:
            self.max(max)

    def min(self, length, msg=None):
        """
        Set minimum array length constraint.

        Args:
            length: Minimum number of elements required.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: len(v) >= length, msg or f"too few items, at least {length}")

    def max(self, length, msg=None):
        """
        Set maximum array length constraint.

        Args:
            length: Maximum number of elements allowed.
            msg: Optional custom error message. Defaults to auto-generated message.

        Returns:
            Self for method chaining.
        """
        return self.refine(lambda v: len(v) <= length, msg or f"too many items, at most {length}")

    def clone(self):
        new = super().clone()
        new._shape = self._shape
        return new

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
    """
    Validator for object/dictionary values.

    Validates that a value is a dictionary and that all fields match
    their corresponding schema validators. Unknown keys are allowed
    by default but can be rejected with strict mode.
    """

    def __init__(self, shape, *, strict=False):
        """
        Initialize object validator with field schemas.

        Args:
            shape: Dictionary mapping field names to their validator schemas.
            strict: If True, reject unknown keys. Defaults to False.
        """
        super().__init__()
        self._shape = shape
        self._strict = strict

    def clone(self):
        new = super().clone()
        new._shape = dict(self._shape)
        new._strict = self._strict
        return new

    @property
    def strict(self):
        """
        Enable strict mode to reject unknown keys.

        When strict mode is enabled, any keys in the input that are
        not defined in the schema will cause a ValidationError.

        Returns:
            Self for method chaining.
        """
        self._strict = True
        return self

    @property
    def shape(self):
        """The field schemas defined for this object validator, as independent copies."""
        return {key: validator.clone() for key, validator in self._shape.items()}

    def extend(self, shape: "dict[str, Validator]") -> "Object":
        """
        Return a new Object validator with additional fields merged in.

        The original validator is not modified. Fields in shape override
        existing fields with the same key.

        Args:
            shape: Dictionary mapping field names to their validator schemas.

        Returns:
            A new Object validator with the combined shape.
        """
        new = self.clone()
        new._shape = self._shape | shape
        return new

    def partial(self, keys=None):
        """
        Return a new Object validator with some or all fields made optional.

        Args:
            keys: List of field names to make optional. If omitted, all fields
                  become optional.

        Returns:
            A new Object validator with the specified fields marked as optional.
        """
        return self.extend(
            {n: v.optional for n, v in self.shape.items() if keys is None or n in keys}
        )

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
                raw = val.get(key, _MISSING)
                if raw is _MISSING and schema._optional and schema._default is _MISSING:
                    continue
                out[key] = schema.parse(raw)
            except ValidationError as error:
                raise ValidationError(f"{key}: {error}") from error
        return self._run_checks(out)


class Record(Validator):
    """
    Validator for dictionaries with arbitrary keys and typed values.

    Validates that a value is a dictionary where all keys match the key
    schema and all values match the value schema.
    """

    def __init__(self, key, value):
        super().__init__()
        self._key = key
        self._value = value

    def clone(self):
        new = super().clone()
        new._key = self._key
        new._value = self._value
        return new

    def _parse(self, val):
        if not isinstance(val, dict):
            raise ValidationError(f"expected dict, got {type(val).__name__}")
        out = {}
        for k, v in val.items():
            try:
                key = self._key.parse(k)
            except ValidationError as error:
                raise ValidationError(f"key {k!r}: {error}") from error
            try:
                out[key] = self._value.parse(v)
            except ValidationError as error:
                raise ValidationError(f"[{k!r}]: {error}") from error
        return self._run_checks(out)


class Number(Float):
    """Validator for numeric values that preserves int vs float type."""

    def _parse(self, val):
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValidationError(f"expected number, got {type(val).__name__}")
        return self._run_checks(val)


class Union(Validator):
    """
    Validator for union/alternative types.

    Validates that a value matches at least one of the provided schemas.
    Tries each schema in order until one succeeds. If all fail, reports
    all validation errors.
    """

    def __init__(self, *schemas):
        """
        Initialize union validator with alternative schemas.

        Args:
            *schemas: Two or more validator schemas to try.
        """
        super().__init__()
        self._schemas = list(schemas)

    def clone(self):
        new = super().clone()
        new._schemas = list(self._schemas)
        return new

    def _parse(self, val):
        errors = []
        for schema in self._schemas:
            try:
                return schema.parse(val)
            except ValidationError as error:
                errors.append(str(error))
        raise ValidationError("no variant matched:\n" + "\n".join(f"  - {e}" for e in errors))


class z:  # pylint: disable=invalid-name
    """
    Main API namespace providing shortcuts to all validators.

    This class provides a clean, concise API for creating validators.
    All validator classes are exposed as lowercase class attributes.

    Attributes:
        string: String validator (z.string()).
        integer: Integer validator (z.integer()).
        float: Float/number validator (z.float()).
        number: Alias for float validator (z.number()).
        boolean: Boolean validator (z.boolean()).
        literal: Literal/enum validator (z.literal()).
        array: Array/list validator (z.array()).
        object: Object/dict validator (z.object()).
        union: Union/alternative validator (z.union()).
    """

    string = String
    integer = Integer
    float = Float
    number = Number
    boolean = Boolean
    literal = Literal
    array = Array
    object = Object
    record = Record
    union = Union
