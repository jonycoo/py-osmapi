import os
import logging
import osmose
from telegram import *
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    TOKEN = os.environ['TEST_BOT']
except KeyError:
    logger.exception('no "TEST_BOT" token in environment variables.', 'Exit program')
    exit()


CHOOSING, TYPING_REPLY, CANCEL = range(3)
reply_keyboard = [['OSM-Name', 'Language', 'Cancel']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    help(update, context)


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Send me a location, I will give you some Issues near this location.',
                              'send /user <username> ,'
                              ' I will give you some Issues where this user was the last editor')
    
    
def location(update: Update, context):
    loc: Location = update.message.location
    issues = osmose.Issue.gen_issue(osmose.get_issues_loc(loc.latitude, loc.longitude))
    for issue in issues:
        send_issue(update.message.bot, update.effective_chat.id, issue)
    logger.info('executed location() method in bot.py')


def user_issue(update: Update, context):
    user = context.args[0]
    issues = osmose.Issue.gen_issue(osmose.get_issues_user(user))
    for issue in issues:
        send_issue(update.message.bot, update.effective_chat.id, issue)
    logger.info('executed user_issue() method in bot.py')


def send_issue(bot: Bot, chat_id, issue: osmose.Issue):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Location', callback_data=issue.id),
                                      InlineKeyboardButton('Welt', callback_data=5)]])

    bot.sendMessage(chat_id, issue.__str__(), reply_markup=keyboard)


def button(update: Update, context):
    query: CallbackQuery = update.callback_query
    query.answer()
    query.edit_message_text('selected ..')
    print(query.data)
    issue = osmose.get_issue(query.data)
    query.bot.sendLocation(update.effective_chat.id, issue.lat, issue.lon,
                           reply_to_message_id=query.message.message_id)


def settings(update, context):
    logger.info(context.user_data)
    if len(context.user_data) > 1:
        update.message.reply_text('the setting are set, please change')
    else:
        update.message.reply_text('you are in the Settings', reply_markup=markup)
    
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


def cancel(update, context):
    logger.info('cancel Settings Conversation')
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
        entry_points=[CommandHandler('settings', settings)],
        states={
             CHOOSING: [MessageHandler(Filters.regex('^(OSM-Name|Language)$'), set_choice)],
             TYPING_REPLY: [MessageHandler(Filters.text, received_info)]
             },
        fallbacks=[MessageHandler(Filters.regex('^Cancel$'), cancel)],
        conversation_timeout=50)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('user', user_issue))
    #dp.add_handler(set_handler)
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.location, location))

    # on non-command i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    #issue_lst = osmose.Issue.gen_issue(osmose.get_issues_user('jonycoo'))
    #send_issue(dp.bot, '343129198', next(issue_lst))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
