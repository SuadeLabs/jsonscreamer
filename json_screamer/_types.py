from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import Optional as _Optional

_Schema = _Dict[str, _Any]
_Validator = _Callable[[_Any], bool]
_Compiler = _Callable[[_Schema], _Optional[_Validator]]

__all__ = ["_Compiler", "_Schema", "_Validator"]
