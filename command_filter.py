import re
from future.utils import string_types
from telegram.ext import BaseFilter
from telegram import MessageEntity


class RegexCommandFilter(BaseFilter):
    data_filter = True

    def __init__(self, pattern, context_name='command_match'):
        if isinstance(pattern, string_types):
            pattern = re.compile(pattern)
        self.pattern = pattern
        self.name = 'RegexCommandFilter({})'.format(self.pattern)
        self.context_name = context_name

    def filter(self, message):
        if not (message.entities
                and message.entities[0].type == MessageEntity.BOT_COMMAND
                and message.entities[0].offset == 0):
            return {}

        command = message.text[1:message.entities[0].length]
        command, _, username = command.partition('@')
        if username and not username.lower() == message.bot.username.lower():
            return {}

        match = self.pattern.search(command)
        if match:
            match = message[match.end():]
            return {self.context_name: match}
        return {}
