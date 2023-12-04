import os
import logging

__version__ = "0.1"
__author__ = "https://github.com/D35YNC"

logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG", '0') != '0' else logging.INFO,
                    format="%(asctime)s | %(name)-24s %(levelname)-8s %(funcName)-10s %(message)s")
