import logging
import sys

from config.settings import DEBUG


def setup_logging():
    level = logging.DEBUG if DEBUG else logging.INFO
    fmt = '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)
    return logging.getLogger("loja")
