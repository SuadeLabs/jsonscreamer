from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from typing import NamedTuple


class _Error(NamedTuple):
    absolute_path: list[str | int]
    message: str
    type: str = ""


_Schema = _Dict[str, _Any]
_Result = _Tuple[bool, _Optional[_Error]]
_Validator = _Callable[[_Any, list[str | int]], _Result]
_Compiler = _Callable[[_Schema, bool], _Optional[_Validator]]


__all__ = ["_Compiler", "_Result", "_Schema", "_Validator"]
