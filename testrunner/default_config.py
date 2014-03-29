"""
Deault config
"""
import sys

from pyinotify import (  # pylint: disable=E0611
    ALL_EVENTS, IN_ACCESS, IN_OPEN,
    IN_ATTRIB, IN_ISDIR, IN_CLOSE_NOWRITE
)
# Global
LOG_LEVEL = "INFO"
CONFIG = "config.py"  # name of local config file

# Watcher
WATCH_DIR = "."
EXCLUDE_FILTER = [
    r'.*\.tmp$',
    r'.*/\.',
    r'.*\.pyc$',
]
EVENTS_INCLUDE = ALL_EVENTS
EVENTS_EXCLUDE = [
    IN_ACCESS,
    IN_OPEN,
    IN_ATTRIB,
    IN_ISDIR,
    IN_CLOSE_NOWRITE,
]
RUNNER_DELAY = 2

# Test runner
TEST_RUNNER = "python -m unittest"
TEST_RUNNER_OPTIONS = "discover"
TESTS = ""
TESTS_OPTIONS = ""
TEST_SUITE = None
TEST_SUITE_OPTIONS = ""

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)-7s %(message)s'
        },
        'simple': {
            'format': '%(levelname)-7s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'simple',
        },
    },
    'loggers': {
        'testrunner': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        }
    }
}
