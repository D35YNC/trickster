import logging

LOG_FORMAT_STRING = "%(asctime)s | %(name)-24s %(levelname)-8s %(funcName)-10s %(message)s"


def create_full_logger(name):
    lg = logging.getLogger(name)
    lg.setLevel(logging.DEBUG)
    lg.addHandler(create_stream_handler())
    # lg.addHandler(create_file_handler())
    return lg


def create_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
    return stream_handler


def create_file_handler():
    file_handler = logging.FileHandler("trickster.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
    return file_handler
