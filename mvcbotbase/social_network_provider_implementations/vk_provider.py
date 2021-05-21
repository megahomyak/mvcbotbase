import random
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import aiohttp
from simple_avk import SimpleAVK

from mvcbotbase import (
    SocialNetworkProvider, OutgoingMessage, AbstractIncomingMessage,
    AbstractIncomingAttachment, AttachmentType
)

# WARNING!!!
# WARNING!!!
#
# BAD CODE BELOW!!!!!


DEFAULT_CHUNK_SIZE = 1024

SYMBOLS_PER_MESSAGE = 4096

MAX_RES_PHOTO_TYPE = "y"  # Don't ask. This is VK territory


class ContentCantBeDownloadedError(Exception):
    pass


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


class UndownloadableVKAttachment(AbstractIncomingAttachment):

    async def download(self, path=None) -> Optional[bytes]:
        raise ContentCantBeDownloadedError()


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
        UndownloadableVKAttachment(AttachmentType.AUDIO)
    ),
    "video": lambda attachment_info, aiohttp_session: (
        UndownloadableVKAttachment(AttachmentType.VIDEO)
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


class VKProvider(SocialNetworkProvider):

    def __init__(self, token: str, group_id: int = None):
        self._token = token
        self._group_id = group_id
        self._vk = None

    # noinspection PyShadowingNames
    # Just for one lambda
    async def get_messages(self) -> AsyncGenerator[
            AbstractIncomingMessage, None
    ]:
        async with aiohttp.ClientSession() as aiohttp_session:
            vk = SimpleAVK(aiohttp_session, self._token, self._group_id)
            self._vk = vk
            async for event in vk.listen():
                if event["type"] == "message_new":
                    message = event["object"]["message"]
                    if (
                        message["attachments"]
                        and message["attachments"]["type"] == "sticker"
                    ):
                        # We're dealing with a sticker. Sticker is an attachment
                        # in VK API, but not in my library.
                        sticker_id = (
                            message["attachments"][0]["sticker"]["sticker_id"]
                        )
                        attachments = []
                    else:
                        sticker_id = None
                        attachments = [
                            attachment_type_generators_lookup_dict.get(
                                attachment["type"], (
                                    lambda attachment_info, aiohttp_session:
                                    UndownloadableVKAttachment(
                                        AttachmentType.OTHER
                                    )
                                )  # Oh shit
                            )(attachment, aiohttp_session)
                            for attachment in message["attachments"]
                        ]
                    yield AbstractIncomingMessage(
                        id=message["id"], text=message["text"],
                        sender_id=message["from_id"],
                        peer_id=message["peer_id"], sticker_id=sticker_id,
                        attachments=attachments
                    )

    async def send_message(self, message: OutgoingMessage):
        text_parts = (
            message.text[i:i + SYMBOLS_PER_MESSAGE]
            for i in range(0, len(message.text), SYMBOLS_PER_MESSAGE)
        )
        for part in text_parts:
            # noinspection SpellCheckingInspection
            await self._vk.call_method(
                "messages.send",
                {
                    "peer_id": message.peer_id,
                    "message": part,
                    "random_id": random.randint(-1_000_000, 1_000_000),
                    "disable_mentions": 1,
                    "dont_parse_links": 1
                }
            )
