import json

from mvcbotbase import (
    MVCBotBase, WordArg, AbstractIncomingMessage, IntArg
)
from mvcbotbase.social_network_provider_implementations.vk_provider import (
    VKProvider
)

config = json.load(open("config.json"))

mvc_bot_base = MVCBotBase(VKProvider(config["token"], config["group_id"]))


# noinspection PyUnusedLocal
@mvc_bot_base.add_command(
    "test", [WordArg("first arg name"), IntArg("second arg name")],
    "test description", "Test group"
)
async def test_handler(
        message: AbstractIncomingMessage, first_arg: str, second_arg: int):
    return "Hello"


@mvc_bot_base.add_command("test2")
async def test_forwarded_messages(message):
    return message.make_answer(forwarded_messages_ids=[message.id])


@mvc_bot_base.add_command("test3")
async def test_reply(message):
    return message.make_reply("abc")


# noinspection PyUnusedLocal
@mvc_bot_base.add_command("help")
async def get_help(message):
    return mvc_bot_base.help_message


mvc_bot_base.run()
