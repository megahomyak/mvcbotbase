import re
from abc import ABC, abstractmethod
from typing import Any, Type


class BaseArg(ABC):

    regex: str

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def get_value(self, argument_text) -> Any:
        pass


class StringArg(BaseArg):

    regex = ".+"

    def get_value(self, argument_text) -> Any:
        return argument_text


class IntArg(BaseArg):

    regex = r"\d+"

    def get_value(self, argument_text) -> Any:
        return int(argument_text)


class WordArg(BaseArg):

    regex = r"\w+"

    def get_value(self, argument_text) -> Any:
        return argument_text


class Sequence(BaseArg):

    def __init__(
            self, name, contents_type: Type[BaseArg],
            sequence_elements_separator):
        super().__init__(name)
        self.contents_type = contents_type
        self.separator = re.compile(sequence_elements_separator)
        self.regex = (
            f"{self.contents_type.regex}"
            f"(?:{sequence_elements_separator}{self.contents_type.regex})*"
        )

    def get_value(self, argument_text) -> Any:
        # noinspection PyTypeChecker
        # because None is a stub for name
        return [
            self.contents_type(None).get_value(element_str)
            for element_str in self.separator.split(argument_text)
        ]
