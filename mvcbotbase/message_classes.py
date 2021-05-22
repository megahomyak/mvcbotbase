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
class Attachment:
    type: AttachmentType


class ContentCantBeDownloadedError(Exception):
    pass


class AbstractIncomingAttachment(Attachment, ABC):

    @abstractmethod
    async def download(self, path=None) -> Optional[bytes]:
        """
        Should return BytesIO if path is not specified,
        should raise ContentCantBeDownloadedError if attachment is not
        downloadable
        """
        pass


@dataclass
class OutgoingAttachment(Attachment):
    file: BytesIO


@dataclass
class AbstractIncomingMessage(ABC):
    peer_id: int
    id: Optional[int] = None
    text: Optional[str] = None
    sender_id: Optional[int] = None
    sticker_id: Optional[int] = None
    attachments: Optional[List[AbstractIncomingAttachment]] = None

    @abstractmethod
    async def get_reply_message(self) -> "AbstractIncomingMessage":
        pass

    @abstractmethod
    async def get_forwarded_messages(self) -> List["AbstractIncomingMessage"]:
        pass


@dataclass
class OutgoingMessage:
    peer_id: int
    text: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    sticker_id: Optional[int] = None
    forwarded_messages_ids: Optional[Iterable[int]] = None
    attachments: Optional[List[OutgoingAttachment]] = None
