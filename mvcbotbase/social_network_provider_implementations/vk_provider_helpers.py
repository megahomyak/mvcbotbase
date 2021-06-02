# WARNING!!!
# WARNING!!!
#
# BAD CODE BELOW!!!!!
from dataclasses import dataclass
from typing import Optional, List, Tuple

import aiohttp

from mvcbotbase import (
    AbstractIncomingAttachment, UndownloadableAttachment,
    AttachmentType, AbstractIncomingMessage
)

DEFAULT_CHUNK_SIZE = 1024

SYMBOLS_PER_MESSAGE = 4096


MAX_RES_PHOTO_TYPE = "y"  # Don't ask. This is VK territory


@dataclass
class DownloadableVKAttachment(AbstractIncomingAttachment):
    link: str
    aiohttp_session: aiohttp.ClientSession

    async def download(self, path=None) -> Optional[bytes]:
        response = await self.aiohttp_session.get(self.link)
        if path:
            with open(path, 'wb') as f:
                while True:
                    chunk = await response.content.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
        else:
            return await response.read()


@dataclass
class PhotoVKAttachment(AbstractIncomingAttachment):
    sizes: list
    aiohttp_session: aiohttp.ClientSession

    async def download(self, path=None) -> Optional[bytes]:
        for attachment_info in self.sizes:
            if attachment_info["type"] == MAX_RES_PHOTO_TYPE:
                return await (
                    await self.aiohttp_session.get(attachment_info["url"])
                ).read()


attachment_type_generators_lookup_dict = {
    "audio": lambda attachment_info, aiohttp_session: (
        UndownloadableAttachment(AttachmentType.AUDIO)
    ),
    "video": lambda attachment_info, aiohttp_session: (
        UndownloadableAttachment(AttachmentType.VIDEO)
    ),
    "photo": lambda attachment_info, aiohttp_session: (
        PhotoVKAttachment(
            AttachmentType.PICTURE,
            sizes=attachment_info["photo"]["sizes"],
            aiohttp_session=aiohttp_session
        )
    ),
    "doc": lambda attachment_info, aiohttp_session: (
        DownloadableVKAttachment(
            AttachmentType.FILE, attachment_info["doc"]["url"], aiohttp_session
        )
    )
}


@dataclass
class IncomingVKMessage(AbstractIncomingMessage):
    _reply_message: Optional["IncomingVKMessage"] = None
    _forwarded_messages: Optional[List["IncomingVKMessage"]] = None

    async def get_reply_message(self) -> AbstractIncomingMessage:
        return self._reply_message

    async def get_forwarded_messages(self) -> List[AbstractIncomingMessage]:
        return self._forwarded_messages


StickerID = Optional[int]


# noinspection PyShadowingNames
# for aiohttp_session
def get_attachments_from_message_info(
    message_info: dict, aiohttp_session
) -> Tuple[StickerID, Optional[List[AbstractIncomingAttachment]]]:
    if (
        message_info["attachments"]
        and message_info["attachments"]["type"] == "sticker"
    ):
        # We're dealing with a sticker. Sticker is an attachment
        # in VK API, but not in my library.
        sticker_id: int = (
            message_info["attachments"][0]["sticker"]["sticker_id"]
        )
        return sticker_id, None
    else:
        attachments = [
            attachment_type_generators_lookup_dict.get(
                attachment["type"], (
                    lambda attachment_info, aiohttp_session:
                    UndownloadableAttachment(AttachmentType.OTHER)
                )  # Oh shit
            )(attachment, aiohttp_session)
            for attachment in message_info["attachments"]
        ]
        return None, attachments


def get_message_from_message_info(
        social_network_provider_id: int,
        message_info: dict, aiohttp_session) -> IncomingVKMessage:
    reply_message = message_info.get("reply_message")
    if reply_message:
        sticker_id, attachments = get_attachments_from_message_info(
            message_info, aiohttp_session
        )
        reply_message = IncomingVKMessage(
            social_network_provider_id=social_network_provider_id,
            id=reply_message["id"], text=reply_message["text"],
            peer_id=reply_message["peer_id"],
            sticker_id=sticker_id,
            sender_id=reply_message["from_id"],
            attachments=attachments
        )
    forwarded_messages = [
        get_message_from_message_info(
            social_network_provider_id, forwarded_message_info, aiohttp_session
        )
        for forwarded_message_info in message_info["fwd_messages"]
    ]
    sticker_id, attachments = get_attachments_from_message_info(
        message_info, aiohttp_session
    )
    return IncomingVKMessage(
        social_network_provider_id=social_network_provider_id,
        id=message_info.get("id"), text=message_info["text"],
        sender_id=message_info["from_id"],
        peer_id=message_info["peer_id"], sticker_id=sticker_id,
        attachments=attachments, _reply_message=reply_message,
        _forwarded_messages=forwarded_messages
    )
