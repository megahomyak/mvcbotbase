import asyncio
import functools
import re
from typing import Callable, Awaitable, Optional, List, Dict, Union, Iterable

from mvcbotbase import helpers
from mvcbotbase.classes_for_command_arguments import BaseArg
from mvcbotbase.command_info import CommandInfo
from mvcbotbase.message_classes import AbstractIncomingMessage, OutgoingMessage
from mvcbotbase.social_network_provider import SocialNetworkProvider
from mvcbotbase.trie import Trie

CommandsGroupName = str
SingleCommandHelpMessage = str


class MVCBotBase:
    """
    The difference between this class and others is in the language of the help
    message
    """

    def __init__(
            self, social_network_providers: (
                Union[List[SocialNetworkProvider], SocialNetworkProvider]
            ),
            command_arguments_separator=" ",
            unknown_command_handler: (
                Optional[Callable[[int, AbstractIncomingMessage], Awaitable]]
            ) = None,
            bad_command_arguments_handler: (
                Optional[Callable[
                    [int, AbstractIncomingMessage, CommandInfo], Awaitable
                ]]
            ) = None,
            handler_errors_handler: (
                Optional[Callable[[CommandInfo, asyncio.Future], Awaitable]]
            ) = None,
            help_message_title="Bot's commands"):
        if isinstance(social_network_providers, SocialNetworkProvider):
            social_network_providers = [social_network_providers]
        self.social_network_providers = social_network_providers
        self.trie = Trie()
        self.command_arguments_separator = command_arguments_separator
        self.command_arguments_separator_length = len(
            command_arguments_separator
        )
        self.unknown_command_handler = unknown_command_handler
        self.bad_command_arguments_handler = bad_command_arguments_handler
        self.handler_errors_handler = handler_errors_handler
        self.command_groups: (
            Dict[CommandsGroupName, List[SingleCommandHelpMessage]]
        ) = {}
        self.ungrouped_command_help_messages: (
            List[SingleCommandHelpMessage]
        ) = []
        self.help_message = None
        self.help_message_title = help_message_title

    # noinspection PyMethodMayBeStatic
    # Because maybe in future I will use `self`
    def make_help_message_for_command(
            self, names, arguments, description) -> str:
        additional_names = ", ".join([
            f"или {name}" for name in names[1:]
        ]) if len(names) > 1 else ""
        arguments = [f"[{arg.name}]" for arg in arguments]
        return " ".join(filter(None, [
            f"/{names[0]}",
            f"({additional_names})" if additional_names else None, *arguments,
            f"- {description}" if description else ""
        ]))

    def _make_full_help_message(self) -> str:
        """
        WARNING!!! Do NOT use this function to make a help message! It is used
        in library to generate the help message ONCE at launch! Generated help
        message is stored in .help_message field of your instance of MVCBotBase.
        If you wanna update help message (for example, you added/removed a
        command in runtime), call .update_message()
        """
        help_message_for_grouped_commands = "\n\n".join(
            f"• {group_name}:\n{helpers.enumerate_and_join_strings(commands)}"
            for group_name, commands in self.command_groups.items()
        )
        return "• {}:\n\n{}".format(
            self.help_message_title,
            "\n\n".join(
                [
                    help_message_for_grouped_commands,
                    helpers.enumerate_and_join_strings(
                        self.ungrouped_command_help_messages
                    )
                ]
                if self.ungrouped_command_help_messages else
                [help_message_for_grouped_commands]
            )
        )

    def add_command(
            self, name_or_names: Union[str, List[str]],
            arguments: List[BaseArg] = None, description=None, group_name=None,
            include_in_help_message=True, handler=None):
        """
        Works as a decorator if handler isn't specified

        group_name is used for help message (it's a command group name)
        """
        if handler:
            if isinstance(name_or_names, str):
                name_or_names = [name_or_names]
            if arguments:
                arguments_regex = re.compile(
                    self.command_arguments_separator.join(
                        f"({argument.regex})" for argument in arguments
                    )
                )
                converters = [argument.get_value for argument in arguments]
            else:
                arguments_regex = None
                converters = None
            command_info = CommandInfo(
                arguments_regex=arguments_regex, handler=handler,
                converters=converters
            )
            for name in name_or_names:
                self.trie.add(name, command_info)
            if include_in_help_message:
                help_message = self.make_help_message_for_command(
                    name_or_names, arguments if arguments else [], description
                )
                if group_name:
                    self.command_groups.setdefault(group_name, []).append(
                        help_message
                    )
                else:
                    self.ungrouped_command_help_messages.append(help_message)
        else:
            return functools.partial(
                self.add_command, name_or_names, arguments, description,
                group_name, include_in_help_message
            )

    def remove_command(
            self, name_or_names: Union[str, Iterable[str]]):
        if isinstance(name_or_names, str):
            self.trie.remove(name_or_names)
        else:
            for name in name_or_names:
                self.trie.remove(name)

    def update_help_message(self) -> None:
        self.help_message = self._make_full_help_message()

    async def run_command_from_message(
            self, incoming_message, social_network_provider):
        command_name_length = incoming_message.text.find(
            self.command_arguments_separator
        )
        if command_name_length == -1:
            command_name = incoming_message.text
            arguments_str = ""
        else:
            command_name = incoming_message.text[:command_name_length]
            arguments_str = incoming_message.text[
                command_name_length + self.command_arguments_separator_length:
            ]
        try:
            command_info = self.trie[command_name]
        except KeyError:
            if self.unknown_command_handler:
                await self.unknown_command_handler(
                    command_name_length, incoming_message
                )
        else:
            if command_info.arguments_regex:
                argument_texts = command_info.arguments_regex.fullmatch(
                    arguments_str
                )
                if not argument_texts:
                    if self.bad_command_arguments_handler:
                        await self.bad_command_arguments_handler(
                            command_name_length, incoming_message, command_info
                        )
                    return
                answer = await command_info.handler(incoming_message, *(
                    converter(argument_text)
                    for argument_text, converter in zip(
                        argument_texts.groups(), command_info.converters
                    )
                ))
            else:
                answer = await command_info.handler(incoming_message)
            if isinstance(answer, OutgoingMessage):
                await social_network_provider.send_message(answer)
            elif answer is not None:
                await social_network_provider.send_message(
                    OutgoingMessage(
                        peer_id=incoming_message.peer_id, text=str(answer)
                    )
                )

    def run(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.update_help_message()
        loop.run_until_complete(asyncio.gather(
            *[
                self._run_social_network_provider(social_network_provider)
                for social_network_provider in self.social_network_providers
            ]
        ))

    async def _run_social_network_provider(self, social_network_provider):
        async for message in social_network_provider.get_messages():
            if self.handler_errors_handler:
                asyncio.create_task(self.run_command_from_message(
                    message, social_network_provider)
                ).add_done_callback(self.handler_errors_handler)
            else:
                asyncio.create_task(
                    self.run_command_from_message(
                        message, social_network_provider
                    )
                )
