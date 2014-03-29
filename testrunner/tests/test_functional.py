from functools import partial
from inspect import getmembers
from mock import patch, ANY, call
from os import path
from time import sleep
from unittest import TestCase

from fixture.io import TempIO
from pyinotify import WatchManager, Notifier

from testrunner import default_config
from testrunner.configurator import Config
from testrunner.watcher import FileChangeHandler


class TestFunctional(TestCase):
    @staticmethod
    def _copy_default_config(mocked_config):
        for name, value in getmembers(default_config):
            if not name.isupper():
                continue

            setattr(mocked_config, name, value)

    @staticmethod
    def _event_generator(events, notifier):
        if not events:
            return True

        path_obj, file_name, data = events.pop(0)
        path_obj.putfile(file_name, data)
        sleep(0.2)

    def setUp(self):
        self.tmp = TempIO(deferred=True)
        self.tmp.conf = "config"
        self.tmp.conf.putfile("__init__.py", "#")
        self.tmp.conf.putfile("config.py", "# config")
        self.tmp.src = "src"
        self.tmp.src.putfile("test.me", "data")

        self.tmp_output = TempIO(deferred=True)

        self.config_file = self.tmp.conf.join("config.py")

    @patch.object(FileChangeHandler, "show_notification", autospec=True)
    @patch("testrunner.configurator.default_config", autospec=True)
    def test_update_code(self, default_config, show_notification):
        out_file = self.tmp_output.join("out.log")
        command_args = [
            "-c", self.config_file,
            "-r", "bash -c 'echo a | tee -a {}'".format(out_file),
            "-d", unicode(self.tmp.src),
        ]
        events = [
            (self.tmp.src, "test_1.me", "some new data"),
            (self.tmp.src, "test_2.me", "some new data"),
        ]

        self._copy_default_config(default_config)
        default_config.RUNNER_DELAY = -1

        wm = WatchManager()
        config = Config(watch_manager=wm, command_args=command_args)
        handler = FileChangeHandler(config=config)
        notifier = Notifier(wm, handler)

        notifier.loop(callback=partial(self._event_generator, events))

        # There are some stupid race conditions (possibly due to the callbacks)
        # Sleep time allows to execute all needed code
        sleep(0.2)

        self.assertTrue(path.exists(self.tmp.src.join("test_1.me")))
        self.assertTrue(path.exists(self.tmp.src.join("test_2.me")))
        self.assertTrue(path.exists(out_file))
        self.assertEqual(show_notification.call_count, 2)
        show_notification.assert_has_calls([call(handler, True, ANY)]*2)

    @patch.object(FileChangeHandler, "show_notification", autospec=True)
    @patch("testrunner.configurator.default_config", autospec=True)
    def test_update_filtered(self, default_config, show_notification):
        out_file = self.tmp_output.join("out.log")
        command_args = [
            "-c", self.config_file,
            "-r", "bash -c 'echo a | tee -a {}'".format(out_file),
            "-d", unicode(self.tmp.src),
        ]
        events = [
            (self.tmp.src, "filtered_1.pyc", "some new data"),
            (self.tmp.src, "filtered_2.tmp", "some new data"),
            (self.tmp.src, ".hidden", "some new data"),
        ]

        self._copy_default_config(default_config)
        default_config.RUNNER_DELAY = -1

        wm = WatchManager()
        config = Config(watch_manager=wm, command_args=command_args)
        handler = FileChangeHandler(config=config)
        notifier = Notifier(wm, handler)

        notifier.loop(callback=partial(self._event_generator, events))

        # There are some stupid race conditions (possibly due to the callbacks)
        # Sleep time allows to execute all needed code
        sleep(0.2)

        self.assertTrue(path.exists(self.tmp.src.join("filtered_1.pyc")))
        self.assertTrue(path.exists(self.tmp.src.join("filtered_2.tmp")))
        self.assertTrue(path.exists(self.tmp.src.join(".hidden")))
        self.assertFalse(path.exists(out_file))
        self.assertFalse(show_notification.called)

    @patch.object(FileChangeHandler, "show_notification", autospec=True)
    @patch("testrunner.configurator.default_config", autospec=True)
    def test_update_conf(self, default_config, show_notification):
        conf_time_1 = path.getmtime(self.tmp.conf.join("config.py"))
        out_file = self.tmp_output.join("out.log")
        command_args = [
            "-c", self.config_file,
            "-r", "bash -c 'echo a | tee -a {}'".format(out_file),
            "-d", unicode(self.tmp.src),
        ]
        events = [
            (self.tmp.conf, "config.py", "# some new data"),
            (self.tmp.conf, "config.py", "# some new data"),
        ]

        self._copy_default_config(default_config)
        default_config.RUNNER_DELAY = -1

        wm = WatchManager()
        config = Config(watch_manager=wm, command_args=command_args)
        handler = FileChangeHandler(config=config)
        notifier = Notifier(wm, handler, timeout=1000)

        notifier.loop(callback=partial(self._event_generator, events))

        # There are some stupid race conditions (possibly due to the callbacks)
        # Sleep time allows to execute all needed code
        sleep(0.2)

        conf_time_2 = path.getmtime(self.tmp.conf.join("config.py"))

        self.assertNotEqual(conf_time_1, conf_time_2)
        self.assertTrue(path.exists(out_file))
        self.assertEqual(show_notification.call_count, 2)

    def tearDown(self):
        del self.tmp
        del self.tmp_output
