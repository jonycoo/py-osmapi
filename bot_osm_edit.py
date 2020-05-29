from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, CallbackQuery
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_CHOICE, TYPING_REPLY = range(3)


class ElemEditor:
    def __init__(self):

        return self.get_conversation()

    def get_conversation(self):
        return ConversationHandler(
            entry_points=[CommandHandler('_edit', self.start)],

            states={
                 CHOOSING: [MessageHandler(Filters.regex('Tag'), self.tag),
                            MessageHandler(Filters.regex('cancel'), self.cancel)
                            ],

                 TYPING_CHOICE: [MessageHandler(Filters.text, self.value)
                                 ],

                 TYPING_REPLY: [MessageHandler(Filters.text, self.edit_info),
                                ],
             },

            fallbacks=[MessageHandler(Filters.regex('^Done$'), self.cancel)]
                                   )

    def start(self):
        pass

    def tag(self):
        pass

    def value(self):
        pass

    def edit_info(self, update: Update, context: CallbackContext):
        value = update.message.text
        context.user_data['edit']
        update.callback_query.edit_message_text()
        return CHOOSING

    def cancel(self):
        pass
