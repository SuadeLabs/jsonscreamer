from typing import Any as _Any, Callable as _Callable, Dict as _Dict

_Schema = _Dict[str, _Any]
_Validator = _Callable[[_Any], bool]
_Compiler = _Callable[[_Schema], _Validator]
