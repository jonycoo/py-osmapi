import os
import logging
import osmose
from telegram import *
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler, CallbackContext)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    TOKEN = os.environ['TEST_BOT']
except KeyError:
    logger.exception('no "TEST_BOT" token in environment variables.', 'Exit program')
    exit()


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
    issues = osmose.get_issues_loc(loc.latitude, loc.longitude)
    for issue in issues:
        send_issue(update.message.bot, update.effective_chat.id, issue)
    logger.info('executed location() method in bot.py')


def user_issue(update: Update, context: CallbackContext):
    logger.debug('Entering: user_issue')
    user = context.args[0]
    issues = osmose.get_issues_user(user)
    pager = osmose.Pager(issues, 10)
    context.user_data['list'] = pager
    send_issues(update.message.bot, update.effective_chat.id, pager)
    logger.info('executed user_issue() method in bot.py')


def send_issue(bot: Bot, chat_id, issue: osmose.Issue):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Location', callback_data=issue.id),
                                      InlineKeyboardButton('Welt', callback_data=5)]])

    bot.send_message(chat_id, issue.__str__(), reply_markup=keyboard)


def prepKeyboard(iss_lst):
    #erstelle ein button je item in iss_lst aber max 5 je zeile
    keyboard = ''
    prep_keyboard = [[InlineKeyboardButton("Prev", callback_data='prev'),
                      InlineKeyboardButton("Next", callback_data='next')]]
    buttons = []
    for i in range(len(iss_lst.curr())):
        buttons.append(InlineKeyboardButton(str(i), callback_data=str(i)))
    for i in range(0, len(buttons), 5):
        prep_keyboard.append(buttons[i:i + 5])

    return InlineKeyboardMarkup(prep_keyboard)


def send_issues(bot: Bot, chat_id, pager):
    logger.debug('Entering: send_issues')
    pager.next()
    keyboard = prepKeyboard(pager)
    bot.send_message(chat_id, osmose.Pager.to_msg(pager.curr()), reply_markup=keyboard)


def next_iss(query, context: CallbackContext):
    logger.debug('in next_iss')
    nx_pg = context.user_data['list'].next()
    iss_msg = osmose.Pager.to_msg(nx_pg)
    query.edit_message_text(iss_msg, reply_markup=prepKeyboard(context.user_data['list']))


def prev_iss(query: CallbackQuery, context: CallbackContext):
    logger.debug('in prev_iss')
    pv_pg = context.user_data['list'].prev()
    iss_msg = osmose.Pager.to_msg(pv_pg)
    query.edit_message_text(iss_msg, reply_markup=prepKeyboard(context.user_data['list']))


def more_iss(query, context: CallbackContext):
    '''reply more details of the Issue'''
    logger.debug('in more_iss')
    lst = context.user_data['list'].curr()
    iss = osmose.get_issue(lst[int(query.data)].id)
    query.edit_message_text(str(iss))


def iss_loc(query):
    issue = osmose.get_issue(query.data)
    query.bot.sendLocation(query.chat_instance, issue.lat, issue.lon,
                           reply_to_message_id=query.message.message_id)


def button(update: Update, context):
    query: CallbackQuery = update.callback_query

    if query.data == 'next':
        next_iss(query, context)
    elif query.data == 'prev':
        prev_iss(query, context)
    else:
        more_iss(query, context)
    query.answer()
    print(query.data)


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

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('user', user_issue))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.location, location))

    # on non-command i.e message - echo the message on Telegram
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
