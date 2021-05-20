import re
from dataclasses import dataclass
from typing import Callable, Coroutine


@dataclass
class CommandInfo:
    regex: re.Pattern
    converters: list
    handler: Callable[..., Coroutine]
