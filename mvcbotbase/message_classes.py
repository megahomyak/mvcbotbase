from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IncomingAttachment:
    attachment_link: Optional[str]
    attachment_contents: Optional[str]
    # attachment_link or attachment_contents should be available


@dataclass
class IncomingMessage(ABC):
    id: int
    text: str
    sender_id: int
    peer_id: int
    reply_message: Optional['IncomingMessage']
    forwarded_messages: List['IncomingMessage']
    attachments: List[IncomingAttachment]

    @abstractmethod
    def as_json(self) -> dict:
        pass
