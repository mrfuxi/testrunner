import logging
from time import time
from os import path
from multiprocessing import Pool

import pyinotify

try:
    # pynotify can not be accessed from virtualenv :(
    import pynotify  # pylint: disable=import-error
except ImportError:
    from nosenotify import adapters as pynotify

from configurator import Config
from runner import Runner

_log = logging.getLogger(__name__)

pynotify.init("basic")


class FileChangeHandler(pyinotify.ProcessEvent):
    def my_init(self, config):
        self._pool = Pool(1)
        self._atask = None
        self._started = 0
        self._last_event = 0
        self.delay = 2
        self.config = config

        self.config.load_config()
        self.test_runner = Runner()
        self.last_result = None

        self.pevent = self.exclude_filter_wrapper

    def task_done(self, callback_result):
        result, info = callback_result
        delta = self._last_event - self._started

        self.show_notification(result, info)

        if delta > self.delay:
            self.start_tests_async()

    def start_tests_async(self, event=None):
        if self._atask and not self._atask.ready():
            #print "Not ready yet:", event
            return

        _log.debug("Run test because of %r", event)
        self._started = time()
        test_cmd = self.config.tests_command()
        suite_cmd = self.config.tests_command(suite=True)
        self._atask = self._pool.apply_async(self.test_runner,
                                             [test_cmd, suite_cmd],
                                             callback=self.task_done)

    def process_default(self, event):
        # on DELETE file will not exits any more
        if path.exists(event.pathname) and \
                path.exists(self.config.config_file()) and \
                path.samefile(event.pathname, self.config.config_file()):
            self.config.load_config()

        self._last_event = time()
        self.start_tests_async(event)

    def exclude_filter_wrapper(self, event):
        return self.config.filter_wrapper(event.pathname)

    def show_notification(self, result, info):
        if self.last_result == result:
            return

        self.last_result = result

        ico = ""
        if result is True:
            ico = "dialog-info"

        notification = pynotify.Notification("Test runner", info, ico)
        notification.show()


def watch():
    _log.info("Start watching")

    wmgr = pyinotify.WatchManager()
    config = Config(watch_manager=wmgr)

    handler = FileChangeHandler(config=config)
    notifier = pyinotify.ThreadedNotifier(wmgr, handler)

    notifier.loop()
