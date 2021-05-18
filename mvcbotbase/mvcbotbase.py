import asyncio
import functools
import re
from typing import Callable, Awaitable, Optional, List

from classes_for_command_arguments import BaseArg
from command_info import CommandInfo
from message_classes import IncomingMessage, OutgoingMessage
from social_network_provider import SocialNetworkProvider
from trie import Trie


class MVCBotBase:

    def __init__(
            self, social_network_providers: List[SocialNetworkProvider],
            command_arguments_separator=" ",
            unknown_command_handler: (
                Optional[Callable[[int, IncomingMessage], Awaitable]]
            ) = None,
            bad_command_arguments_handler: (
                Optional[
                    Callable[[int, IncomingMessage, CommandInfo], Awaitable]
                ]
            ) = None,
            handler_errors_handler: (
                Optional[Callable[[CommandInfo, asyncio.Future], Awaitable]]
            ) = None):
        self.social_network_providers = social_network_providers
        self.trie = Trie()
        self.command_arguments_separator = command_arguments_separator
        self.command_arguments_separator_length = len(
            command_arguments_separator
        )
        self.unknown_command_handler = unknown_command_handler
        self.bad_command_arguments_handler = bad_command_arguments_handler
        self.handler_errors_handler = handler_errors_handler

    def add_command(self, name, arguments: List[BaseArg] = None, handler=None):
        """
        Works as a decorator if handler isn't specified
        """
        if handler:
            self.trie.add(name, CommandInfo(
                regex=re.compile(self.command_arguments_separator.join(
                    (name, *(argument.regex for argument in arguments))
                )),
                handler=handler,
                converters=[argument.get_value for argument in arguments]
            ))
        else:
            return functools.partial(self.add_command, name, arguments)

    async def run_command_from_message(
            self, incoming_message, social_network_provider):
        command_name_length = incoming_message.text.find(
            self.command_arguments_separator
        )
        try:
            command_info = self.trie[
                incoming_message.text[:command_name_length]
                if command_name_length == -1 else
                incoming_message.text
            ]
        except KeyError:
            if self.unknown_command_handler:
                await self.unknown_command_handler(
                    command_name_length, incoming_message
                )
        else:
            argument_texts = command_info.regex.fullmatch(incoming_message.text)
            if argument_texts:
                answer = await command_info.handler(incoming_message, *(
                    converter(argument_text)
                    for argument_text, converter in zip(
                        argument_texts.groups(), command_info.converters
                    )
                ))
                if isinstance(answer, OutgoingMessage):
                    await social_network_provider.send_message(answer)
                elif answer is not None:
                    await social_network_provider.send_message(
                        OutgoingMessage(
                            peer_id=incoming_message.peer_id, text=str(answer)
                        )
                    )
            else:
                if self.bad_command_arguments_handler:
                    await self.bad_command_arguments_handler(
                        command_name_length, incoming_message, command_info
                    )

    def run(self):
        asyncio.run(self.async_run())

    async def _run_social_network_provider(self, social_network_provider):
        async for message in social_network_provider.get_messages():
            if self.handler_errors_handler:
                asyncio.create_task(self.run_command_from_message(
                    message, social_network_provider)
                )
            else:
                asyncio.create_task(
                    self.run_command_from_message(
                        message, social_network_provider
                    )
                ).add_done_callback(self.handler_errors_handler)

    async def async_run(self):
        for social_network_provider in self.social_network_providers:
            asyncio.create_task(
                self._run_social_network_provider(social_network_provider)
            )
