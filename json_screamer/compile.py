from typing import Dict as _Dict
from ._types import _Compiler, _Schema, _Validator


__COMPILATION_FUNCTIONS: _Dict[str, _Compiler] = {}


def register(compiler: _Compiler) -> _Compiler:
    """Register a compiler for compiling a given type."""
    type_ = compiler.__name__.rstrip("_")
    __COMPILATION_FUNCTIONS[type_] = compiler
    return compiler


def compile_(defn: _Schema) -> _Validator:
    """Compile a schema definition returning a validator."""
    return __COMPILATION_FUNCTIONS[defn["type"]](defn)
