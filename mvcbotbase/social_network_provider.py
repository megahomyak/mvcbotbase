from abc import ABC, abstractmethod
from typing import AsyncGenerator

from mvcbotbase.message_classes import AbstractIncomingMessage, OutgoingMessage


class SocialNetworkProvider(ABC):

    @abstractmethod
    async def get_messages(self) -> AsyncGenerator[
            AbstractIncomingMessage, None
    ]:
        yield

    @abstractmethod
    async def send_message(self, message: OutgoingMessage):
        pass
