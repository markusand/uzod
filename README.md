# uzod

**uzod** is a lightweight validation library inspired by [zod](https://github.com/colinhacks/zod) for (micro)python that provides runtime type checking and validation with a clean, chainable API.

## Features

**🦾 Ergonomic API** - Fluent, chainable interface

**🛡️ Type-safe** - Comes with complete type stubs for IDE support

**🪶 Lightweight** - Zero dependencies, single file (~220 lines)

**🤸🏻 Flexible** - Built-in validators + custom refinements

**🧩 Composable** - Build complex schemas from simple primitives

## Installation

Just copy `uzod.py` into your project - it's standalone!

## Quick Start

```python
from uzod import z, ValidationError

# Define a schema
user_schema = z.object({
    "name": z.string(min=2, max=50),
    "email": z.string().refine(lambda s: "@" in s, "invalid email"),
    "age": z.integer(min=0, max=120).optional,
})

# Validate data
try:
    user = user_schema.parse({
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30
    })
    print(user)  # {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}
except ValidationError as error:
    print(f"Validation failed: {error}")
```

## API Reference

### String

```python
z.string()                   # Any string
z.string(min=3)              # At least 3 characters
z.string(max=100)            # At most 100 characters
z.string(min=3, max=100)     # Between 3-100 characters
```

### Integer

```python
z.integer()                 # Any integer
z.integer(min=0)            # Non-negative
z.integer(min=1, max=10)    # Between 1-10
```

### Float

```python
z.float()                   # Any float
z.float(min=0.0)            # Non-negative
z.float(min=0.0, max=1.0)   # Between 0.0-1.0
```

### Boolean

```python
z.boolean()                 # true or false
```

### Literal

```python
z.literal("admin", "user")  # Must be "admin" or "user"
z.literal(1, 2, 3)          # Must be 1, 2, or 3
```

### Array

```python
z.array(z.string())                  # Array of strings
z.array(z.integer(), min=1, max=10)  # 1-10 integers
z.array(z.object({...}))             # Array of objects
```

### Object

```python
z.object({
    "name": z.string(),
    "age": z.integer()
})

# Strict mode - reject unknown keys (can also be used with chainable method)
z.object({"name": z.string()}, strict=True)
```

### Union

```python
z.union(z.string(), z.integer())     # String OR integer
z.union(z.literal("yes", "no"), z.boolean())
```

### Modifiers

#### Optional

```python
# Field can be omitted (returns None)
z.object({
    "name": z.string(),
    "nickname": z.string().optional
})

# parse({"name": "Alice"}) -> {"name": "Alice", "nickname": None}
```

#### Nullable

```python
# Field can be None
z.object({
    "name": z.string().nullable
})

# parse({"name": None}) -> {"name": None}
```

#### Default

```python
# Provide default value when field is missing or None
z.object({
    "role": z.string().default("user")
})

# parse({}) -> {"role": "user"}
```

#### Refine (Custom Validation)

```python
# Add custom validation logic
z.string().refine(lambda s: s.isalnum(), "must be alphanumeric")
z.integer().refine(lambda n: n % 2 == 0, "must be even")
```

## Error Messages

uzod provides helpful error messages:

```python
>>> z.string(min=5).parse("hi")
ValidationError: too short, at least 5 chars

>>> z.integer().parse("123")
ValidationError: expected int, got str

>>> z.object({"name": z.string()}).parse({"name": 123})
ValidationError: name: expected str, got int

>>> z.object({"a": z.string()}, strict=True).parse({"a": "x", "b": "y"})
ValidationError: unexpected keys: b
```

## Contributing

Contributions are welcome! This is a small, focused library - let's keep it that way.
