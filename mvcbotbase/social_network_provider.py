from abc import ABC, abstractmethod
from typing import AsyncGenerator

from mvcbotbase.message_classes import IncomingMessage, OutgoingMessage


class SocialNetworkProvider(ABC):

    @abstractmethod
    async def get_messages(self) -> AsyncGenerator[IncomingMessage, None]:
        yield

    @abstractmethod
    async def send_message(self, message: OutgoingMessage):
        pass
