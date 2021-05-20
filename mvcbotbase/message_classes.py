from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum, auto
from io import BytesIO
from typing import List, Iterable, Optional


class AttachmentType(Enum):
    PICTURE = auto()
    FILE = auto()
    AUDIO = auto()
    VIDEO = auto()
    OTHER = auto()


@dataclass
class IncomingAttachment:
    type: AttachmentType

    @abstractmethod
    async def download(self, path=None) -> Optional[bytes]:
        """
        Should return BytesIO if path is not specified
        """
        pass


@dataclass
class IncomingMessage(ABC):
    peer_id: int
    id: Optional[int] = None
    text: Optional[str] = None
    sender_id: Optional[int] = None
    sticker_id: Optional[int] = None
    attachments: Optional[List[IncomingAttachment]] = None

    @abstractmethod
    async def get_reply_message(self):
        pass

    @abstractmethod
    async def get_forwarded_messages(self):
        pass


@dataclass
class OutgoingMessage(ABC):
    peer_id: int
    text: Optional[str] = None
    answer_to_message_id: Optional[int] = None
    sticker_id: Optional[int] = None
    forwarded_messages_ids: Optional[Iterable[int]] = None

    @abstractmethod
    async def add_attachment(self, attachment: BytesIO):
        pass
