"""Tests for uzod schema validation library"""

import unittest
from uzod import z, ValidationError


class TestUZodValidator(unittest.TestCase):
    """Tests for uzod validators including type validation, constraints, and modifiers"""

    def test_string(self):
        """should validate string with min and max length constraints"""
        schema = z.string(min=3, max=5)

        self.assertEqual(schema.parse("Hello"), "Hello")

        with self.assertRaises(ValidationError) as raised:
            schema.parse("Hi")
        self.assertEqual("too short, at least 3 chars", str(raised.exception))

        with self.assertRaises(ValidationError) as raised:
            schema.parse("Hello World")
        self.assertEqual("too long, at most 5 chars", str(raised.exception))

    def test_integer(self):
        """should validate integer with min and max constraints"""
        schema = z.integer(min=3, max=5)

        self.assertEqual(schema.parse(4), 4)

        with self.assertRaises(ValidationError) as raised:
            schema.parse(2)
        self.assertEqual("too small, at least 3", str(raised.exception))

        with self.assertRaises(ValidationError) as raised:
            schema.parse(6)
        self.assertEqual("too large, at most 5", str(raised.exception))

    def test_float(self):
        """should validate float with min and max constraints"""
        schema = z.float(min=3.0, max=5.0)

        self.assertEqual(schema.parse(4.0), 4.0)

        with self.assertRaises(ValidationError) as raised:
            schema.parse(2.0)
        self.assertEqual("too small, at least 3.0", str(raised.exception))

        with self.assertRaises(ValidationError) as raised:
            schema.parse(6.0)
        self.assertEqual("too large, at most 5.0", str(raised.exception))

    def test_boolean(self):
        """should validate boolean"""
        schema = z.boolean()

        self.assertEqual(schema.parse(True), True)
        self.assertEqual(schema.parse(False), False)

        with self.assertRaises(ValidationError) as raised:
            schema.parse(1)
        self.assertEqual("expected bool, got int", str(raised.exception))

    def test_literal(self):
        """should validate literal values against allowed options"""
        schema = z.literal("foo", "bar")

        self.assertEqual(schema.parse("foo"), "foo")
        self.assertEqual(schema.parse("bar"), "bar")

        with self.assertRaises(ValidationError) as raised:
            schema.parse("baz")
        self.assertEqual("expected one of (foo, bar), got baz", str(raised.exception))

    def test_array(self):
        """should validate array items with length constraints"""
        schema = z.array(z.string(), min=2, max=2)

        self.assertEqual(schema.parse(["foo", "bar"]), ["foo", "bar"])

        with self.assertRaises(ValidationError) as raised:
            schema.parse(["foo", 1])
        self.assertEqual("[1] expected str, got int", str(raised.exception))

        with self.assertRaises(ValidationError) as raised:
            schema.parse(["foo"])
        self.assertEqual("too few items, at least 2", str(raised.exception))

        with self.assertRaises(ValidationError) as raised:
            schema.parse(["foo", "bar", "baz"])
        self.assertEqual("too many items, at most 2", str(raised.exception))

    def test_object(self):
        """should validate object properties against schema"""
        schema = z.object({"foo": z.string()})

        self.assertEqual(schema.parse({"foo": "bar"}), {"foo": "bar"})

        with self.assertRaises(ValidationError) as raised:
            schema.parse({"foo": 1})
        self.assertEqual("foo: expected str, got int", str(raised.exception))

    def test_object_strict(self):
        """should reject unknown keys when strict mode enabled in object (keep optional)"""
        schema = z.object({"name": z.string(), "age": z.integer().optional}, strict=True)

        # Valid object passes
        self.assertEqual(schema.parse({"name": "Alice"}), {"name": "Alice"})

        # Extra keys are rejected
        with self.assertRaises(ValidationError) as raised:
            schema.parse({"name": "Alice", "pet": "Rudolph"})
        self.assertEqual("unexpected keys: pet", str(raised.exception))

    def test_union(self):
        """should validate value against multiple schema variants"""
        schema = z.union(z.integer(), z.literal("foo"))

        self.assertEqual(schema.parse(2), 2)
        self.assertEqual(schema.parse("foo"), "foo")

        with self.assertRaises(ValidationError) as raised:
            schema.parse("bar")
        self.assertEqual(
            "no variant matched:\n  - expected int, got str\n  - expected one of (foo), got bar",
            str(raised.exception),
        )

    def test_nullable(self):
        """should accept None values for nullable fields but still require the key"""
        schema = z.object({"name": z.string().nullable})

        self.assertEqual(schema.parse({"name": "Bob"}), {"name": "Bob"})
        self.assertEqual(schema.parse({"name": None}), {"name": None})

        # Nullable still requires the key to be present
        with self.assertRaises(ValidationError) as raised:
            schema.parse({})
        self.assertEqual("name: required", str(raised.exception))

    def test_optional(self):
        """should allow optional fields to be omitted from objects"""
        schema = z.object({"req": z.string(), "opt": z.string().optional})

        # Optional field can be omitted or provided
        self.assertEqual(schema.parse({"req": "req"}), {"req": "req"})
        self.assertEqual(schema.parse({"req": "req", "opt": "opt"}), {"req": "req", "opt": "opt"})

        # Required field is must be provided
        with self.assertRaises(ValidationError) as raised:
            schema.parse({"opt": "opt"})
        self.assertEqual("req: required", str(raised.exception))

    def test_optional_and_nullable(self):
        """should allow fields to be both optional and accept None"""
        schema = z.object({"field": z.string().optional.nullable})

        self.assertEqual(schema.parse({"field": "foo"}), {"field": "foo"})
        self.assertEqual(schema.parse({"field": None}), {"field": None})
        self.assertEqual(schema.parse({}), {})

    def test_default(self):
        """should use default values when fields are missing or None"""
        schema = z.object({"foo": z.integer().default(18)})

        # Default is used when field is missing or None
        self.assertEqual(schema.parse({}), {"foo": 18})
        self.assertEqual(schema.parse({"foo": None}), {"foo": 18})

        # Provided value takes precedence
        self.assertEqual(schema.parse({"foo": 40}), {"foo": 40})

    def test_refine_validation(self):
        """should allow custom validation logic with refine"""
        schema = z.integer(min=0).refine(lambda n: n % 2 == 0, "must be even")

        self.assertEqual(schema.parse(4), 4)

        # Value onstraint fails
        with self.assertRaises(ValidationError) as raised:
            schema.parse(-2)
        self.assertEqual("too small, at least 0", str(raised.exception))

        # Refine constraint fails
        with self.assertRaises(ValidationError) as raised:
            schema.parse(3)
        self.assertEqual("must be even", str(raised.exception))

    def test_clone(self):
        """should produce independent validators that don't affect each other"""
        base = z.string().min(3)
        cloned = base.clone()

        cloned.max(5)

        # base is unaffected by changes to cloned
        self.assertEqual(base.parse("Hello World"), "Hello World")
        with self.assertRaises(ValidationError):
            cloned.parse("Hello World")

    def test_object_extend(self):
        """should allow extending an object with new schema attributes"""
        base = z.object({"id": z.number(), "name": z.string()})
        with_age = base.extend({"age": z.integer()})
        with_string_id = base.extend({"id": z.string()})
        with_constrained_id = base.extend({"id": base.shape["id"].min(10)})

        self.assertEqual(base.parse({"id": 1, "name": "Alice"}), {"id": 1, "name": "Alice"})

        with self.assertRaises(ValidationError):
            with_age.parse({"id": 1, "name": "Alice"})

        with self.assertRaises(ValidationError):
            with_string_id.parse({"id": 1, "name": "Alice"})

        with self.assertRaises(ValidationError):
            with_constrained_id.parse({"id": 1, "name": "Alice"})

    def test_object_partial(self):
        """should make all or selected fields optional"""
        base = z.object({"id": z.number(), "name": z.string()})
        all_optional = base.partial()
        some_optional = base.partial(["name"])

        self.assertEqual(all_optional.parse({}), {})

        self.assertEqual(some_optional.parse({"id": 1}), {"id": 1})
        with self.assertRaises(ValidationError):
            some_optional.parse({"name": "Bob"})
