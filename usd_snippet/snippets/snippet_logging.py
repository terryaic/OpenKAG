# Logging/Log

# Carbonite logger is used both for python and C++:
import carb
carb.log_info("123")
carb.log_warn("456")
carb.log_error("789")

# For python it is recommended to use std python logging, which also redirected to Carbonite
# It also captures file path and loc
import logging
logger = logging.getLogger(__name__)
logger.info("123")
logger.warning("456")
logger.error("789")
