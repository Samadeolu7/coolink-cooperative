import logging
from logging.handlers import RotatingFileHandler

# Configure the root logger
logging.basicConfig(level=logging.DEBUG)  # Set the default log level

# Create a logger instance
logger = logging.getLogger("lynx")

# Create a file handler
file_handler = RotatingFileHandler("lynx.log", maxBytes=1024, backupCount=3)
file_handler.setLevel(logging.INFO)

# Create a stream handler for console output
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Set formatters for handlers
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
