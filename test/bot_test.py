import os


try:
    TOKEN = os.environ['API_ID']
    TOKEN = os.environ['API_HASH']
except KeyError:
    logger.exception('no "TEST_BOT" token in environment variables.', 'Exit program')
    exit()