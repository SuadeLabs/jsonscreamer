from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import Union as _Union

_Schema = _Union[_Dict[str, _Any], bool]
_Validator = _Callable[[_Any], bool]
