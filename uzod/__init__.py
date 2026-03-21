"""
uzod - Lightweight validation library for (Micro)Python.

This package provides runtime type checking and validation with a clean,
chainable API inspired by Zod. Perfect for MicroPython projects, embedded
systems, or any Python application that needs simple, effective validation
without dependencies.

Exports:
    z: Main API namespace for creating validators
    ValidationError: Exception raised when validation fails
"""

from .uzod import ValidationError, z

__all__ = ["ValidationError", "z"]
