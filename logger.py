import logging

# global logger instance because singletons are cool
_logger = None

def get_logger(name):
    global _logger
    # only create once, reuse for everyone
    if _logger == None:
        _logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    return _logger  # always return same logger regardless of name
