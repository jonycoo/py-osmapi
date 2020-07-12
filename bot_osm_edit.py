from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, DispatcherHandlerStop
from telegram import Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import osm.osm_util
import osm.osm_api
import logging
import io

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TAG_CHOICE, VALUE_REPLY, TYPING_REPLY, LOCATION, TEXT, DESCRIPTION, NAME, GPX_SAVE, SAVE = range(10)


class ElemEditor:
    def __init__(self):
        self.osmapi = osm.osm_api.OsmApi()
        pass

    def get_conversation(self):
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start),
                          MessageHandler(Filters.document, self.gpx_up)],

            states={
                 CHOOSING: [MessageHandler(Filters.regex('tag'), self.tag),
                            ],


                 TAG_CHOICE: [MessageHandler(Filters.text, self.tag)],

                 TYPING_REPLY: [MessageHandler(Filters.text, self.value),
                                MessageHandler(Filters.location, self.location)
                                ],
                NAME: [MessageHandler(Filters.text, self.gpx_name)],

                DESCRIPTION: [CommandHandler('skip', self.gpx_up_content),
                              MessageHandler(Filters.text, self.gpx_desc)],

                GPX_SAVE:[CommandHandler('save', self.gpx_up_content),
                          CallbackQueryHandler(self.gpx_toggles, 0)
                          ]
             },

            fallbacks=[MessageHandler(Filters.regex('cancel'), self.cancel),
                       MessageHandler(Filters.command, self.invalid, 0)]
                                   )

    def start(self, update: Update, context: CallbackContext):
        if update.callback_query.data == 'edit':
            update.callback_query.answer('enter edit conversation')
            try:
                thing = context.user_data['edit']
                # send message containing all tags and values of object
                return TAG_CHOICE
            except KeyError:
                context.bot.send_message(update.effective_chat.id, 'select action')  # for now only Note create
                context.user_data['subject'] = osm.osm_util.Note
                context.bot.send_message(update.effective_chat.id, 'please send location.')
                return TYPING_REPLY
        return  # handled by bot

    def gpx_up(self, update: Update, context):
        data = open(update.effective_message.document.get_file().download()).read()
        context.user_data['gpx'] = osm.osm_util.Trace(None, data, None, None, None)
        update.message.reply_text('please send trace-name.')
        return NAME

    def gpx_name(self, update, context):
        name = update.message.text
        context.user_data['gpx'].name = name
        update.message.reply_text('please write a Description, or use /skip .')
        return DESCRIPTION

    def gpx_desc(self, update, context):
        context.user_data['gpx'].desc = update.message.text
        self.gpx_up_content(update, context)
        return GPX_SAVE

    def gpx_up_content(self, update, context):
        gpx: osm.osm_util.Trace = context.user_data['gpx']
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(gpx.visibility, callback_data='vis'),
                                       InlineKeyboardButton('Upload', callback_data='save')]])
        try:
            update.callback_query.edit_message_text(str(gpx), reply_markup=markup)
        except AttributeError:
            update.message.reply_text(str(gpx), reply_markup=markup)

        return GPX_SAVE

    def gpx_toggles(self, update, context):
        if update.callback_query.data == 'save':
            self.gpx_save(update, context)
            del context.user_data['gpx']
            self.cancel(update, context)
        elif update.callback_query.data == 'vis':
            gpx = context.user_data['gpx']
            vis = ['identifiable', 'trackable', 'public', 'private']
            gpx.visibility = vis[vis.index(gpx.visibility) - 1]
            context.user_data['gpx'] = gpx
        update.callback_query.answer()
        self.gpx_up_content(update, context)
        return GPX_SAVE

    def gpx_save(self, update, context):
        gpx = context.user_data['gpx']
        tid = self.osmapi.upload_gpx(gpx.gpx, gpx.name, gpx.desc, gpx.tags, gpx.visibility)
        update.callback_query.edit_message_text('uploaded track: ' + str(tid))

    def invalid(self, update, context):
        logger.error('invalid command')

    def location(self, update, context):
        loc = update.message.location
        update.message.reply_text('send Note text')
        return TYPING_REPLY

    def tag(self, update, context):
        print('hay here is conversation Tag')
        return CHOOSING

    def value(self):
        pass

    def edit_info(self, update: Update, context: CallbackContext):
        value = update.message.text
        context.user_data['edit']
        update.callback_query.edit_message_text()
        return CHOOSING

    def note(self):
        pass

    def cancel(self, update, context):
        update.callback_query.answer('exit edit conversation')
        return ConversationHandler.END
