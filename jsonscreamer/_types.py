from __future__ import annotations

from typing import (
    Any as _Any,
    Callable as _Callable,
    Dict as _Dict,
    NamedTuple,
    Optional as _Optional,
    Tuple as _Tuple,
)


class _Error(NamedTuple):
    absolute_path: list[str | int]
    message: str
    type: str = ""


_Schema = _Dict[str, _Any]
_Result = _Tuple[bool, _Optional[_Error]]
_Validator = _Callable[[_Any, list[str | int]], _Result]
_Compiler = _Callable[[_Schema, bool], _Optional[_Validator]]


__all__ = ["_Compiler", "_Result", "_Schema", "_Validator"]
