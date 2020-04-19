import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


TOKEN = '819692690:AAGTNDg1DXBQsQkpecrmpIKdOJbLOhXztHc'
channel = '343129198'


CHOOSING, TYPING_REPLY, CANCLE = range(3)

reply_keyboard = [['OSM-Name', 'Language', 'Cancle']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
    
    
def location(update, context):
    """Send location"""
    update.message.reply_location(float(26.1949226),float(127.6955086))
    
#def message(update, context):
    
def settings(update, context):
    #update.message.reply_text('you are in the Settings',reply_markup=markup)
    logger.info(context.user_data)
    if len(context.user_data)>1:
        update.message.reply_text('the setting are set, please change')
        #update.message.reply_text(
            #"You are in the Settings,please return by Cancle or change you settings",
            #"current information:",
            #"Language: {}",
            #"OSM-Name: {}"
            #.format(context.user_data['language'], context.user_data['osm-name']), reply_markup=markup)
    else:
        update.message.reply_text('you are in the Settings',reply_markup=markup)
    
    return CHOOSING
        
    
def set_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'please tell me your {} '.format(text.lower()))
    
    return TYPING_REPLY

def received_info(update, context):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice'].lower()
    user_data[category] = text
    logger.info(user_data)
    
    del user_data['choice']
    
    return CHOOSING
    
def cancle(update, context):
    logger.info('cancle Settings Conversation')
    update.message.reply_text('Exit Settings', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)
    
    

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    set_handler = ConversationHandler(
        entry_points=[CommandHandler('settings',settings)],
        
        states={
             CHOOSING: [MessageHandler(Filters.regex('^(OSM-Name|Language)$'),
                                      set_choice)
                       ],
             TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_info),
                           ]
            },
        fallbacks=[MessageHandler(Filters.regex('^Cancle$'), cancle)]
        )


    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(set_handler)
    

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
