import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler and set the log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s::%(filename)s[%(funcName)s()]::%(levelname)s::%(message)s')
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)