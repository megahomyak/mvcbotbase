import re
from dataclasses import dataclass
from typing import Callable, Coroutine, Optional


@dataclass
class CommandInfo:
    arguments_regex: Optional[re.Pattern]
    converters: list
    handler: Callable[..., Coroutine]
