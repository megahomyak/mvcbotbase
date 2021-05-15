import re
from collections import Callable, Coroutine
from dataclasses import dataclass


@dataclass
class CommandInfo:
    regex: re.Pattern
    converters: list
    handler: Callable[Coroutine]
