# WARNING!!!
# WARNING!!!
#
# BAD CODE BELOW!!!!!
import functools
import random
from dataclasses import dataclass
from typing import AsyncGenerator, Union

import aiohttp
from simple_avk import SimpleAVK

from mvcbotbase import (
    SocialNetworkProvider, OutgoingMessage, AttachmentType, OutgoingAttachment,
    OutgoingFileAttachment, AttachmentToUploadHasUnknownFileTypeError
)
from mvcbotbase.social_network_provider_implementations import (
    vk_provider_helpers as helpers
)

AttachmentString = str


@dataclass
class OutgoingVKMusicAttachment(OutgoingAttachment):
    title: str
    artists_name: str


class VKProvider(SocialNetworkProvider):

    def __init__(
            self, token: str,
            group_id: int = None):
        self._token = token
        self._group_id = group_id
        self._vk = None
        self.aiohttp_session = None

    async def _upload_file(
            self, attachment: OutgoingFileAttachment, peer_id: int,
            upload_vk_method_name: str, save_vk_method_name: str,
            attachment_type: str, additional_data: dict = None,
            is_not_video=True) -> AttachmentString:
        uploading_params = {"peer_id": peer_id}
        if self._group_id:
            uploading_params["group_id"] = self._group_id
        upload_url = (await self._vk.call_method(
            upload_vk_method_name, uploading_params
        ))["upload_url"]
        file_info = await (await self.aiohttp_session.post(upload_url, data={
            ("file" if is_not_video else "video_file"): attachment.file
        })).json()
        print(file_info)
        if is_not_video:
            doc_info = await self._vk.call_method(
                save_vk_method_name, {
                    **additional_data, **file_info
                } if additional_data else file_info
            )
            attachment_info = doc_info[attachment_type]
        else:
            attachment_info = file_info
        return (
            f"{attachment_type}{attachment_info['owner_id']}"
            f"_{attachment_info['id']}"
        )

    async def _upload_attachment_by_type(
            self, attachment: Union[
                OutgoingFileAttachment, OutgoingVKMusicAttachment
            ], peer_id: int):
        """
        SOMEBODY, PLEASE, MAKE THAT FOR ME, I'M TIRED
        """
        upload_function = functools.partial(
            self._upload_file, attachment, peer_id
        )
        if attachment.type is AttachmentType.FILE:
            return await upload_function(
                "docs.getMessagesUploadServer", "docs.save", "doc",
                {"title": attachment.filename}
            )
        elif attachment.type is AttachmentType.PICTURE:
            return await upload_function(
                attachment, "photos.getUploadServer", "photos.save", "photo"
            )
        elif attachment.type is AttachmentType.AUDIO:
            return await upload_function(
                attachment, "audio.getUploadServer", "audio.save", "audio",
                {"title": attachment.title, "artist": attachment.artists_name}
            )
        elif attachment.type is AttachmentType.VIDEO:
            return await upload_function(
                attachment, "video.save", "video.save", "video",
                is_not_video=False
            )
        elif attachment.type is AttachmentType.OTHER:
            raise AttachmentToUploadHasUnknownFileTypeError
        else:
            raise NotImplementedError

    async def get_messages(self) -> AsyncGenerator[
            helpers.IncomingVKMessage, None
    ]:
        async with aiohttp.ClientSession() as aiohttp_session:
            vk = SimpleAVK(aiohttp_session, self._token, self._group_id)
            self._vk = vk
            self.aiohttp_session = vk.aiohttp_session
            async for event in vk.listen():
                if event["type"] == "message_new":
                    yield helpers.get_message_from_message_info(
                        self.__class__,
                        event["object"]["message"], aiohttp_session
                    )

    async def send_message(self, message: OutgoingMessage):
        # noinspection SpellCheckingInspection
        params = {
            "peer_id": message.peer_id,
            "random_id": random.randint(-1_000_000, 1_000_000),
            "disable_mentions": 1,
            "dont_parse_links": 1
        }
        if message.attachments:
            raise NotImplementedError(
                "https://github.com/megahomyak/mvcbotbase/pulls PLEASE I CAN'T "
                "MAKE THIS ANYMORE IT HARMS MY PRODUCTIVITY A LOT"
            )
            # noinspection PyUnreachableCode
            attachment_strings = [
                await self._upload_attachment_by_type(
                    attachment, message.peer_id
                )
                for attachment in message.attachments
            ]
            attachment_string = ",".join(attachment_strings)
        else:
            attachment_string = None
        if message.text:
            text_parts = (
                message.text[i:i + helpers.SYMBOLS_PER_MESSAGE]
                for i in range(
                    0, len(message.text), helpers.SYMBOLS_PER_MESSAGE
                )
            )
            current_message = None
            messages_counter = 0
            while True:
                next_message = next(text_parts, None)
                if current_message:
                    if not next_message:
                        if message.forwarded_messages_ids:
                            # This is the end
                            params["forward_messages"] = ",".join(
                                map(str, message.forwarded_messages_ids)
                            )
                        if attachment_string:
                            params["attachment"] = attachment_string
                    if messages_counter == 1 and message.reply_to_message_id:
                        params["reply_to"] = message.reply_to_message_id
                    params["message"] = current_message
                    await self._vk.call_method("messages.send", params)
                    if not next_message:
                        break
                    del params["message"]
                    for key_name in ("reply_to", "forward_messages"):
                        try:
                            del params[key_name]
                        except KeyError:
                            pass
                current_message = next_message
                messages_counter += 1
        else:
            if message.forwarded_messages_ids:
                params["forward_messages"] = ",".join(
                    map(str, message.forwarded_messages_ids)
                )
            if message.reply_to_message_id:
                params["reply_to"] = message.reply_to_message_id
            if attachment_string:
                params["attachment"] = attachment_string
            await self._vk.call_method("messages.send", params)
