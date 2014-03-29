from unittest import TestCase

from mock import Mock, patch, call
from pyinotify import Event

from testrunner.configurator import Config
from testrunner.watcher import FileChangeHandler, watch


class TestFileChangeHandler(TestCase):

    @patch("testrunner.watcher.Runner", autospec=True)
    @patch("testrunner.watcher.Pool", autospec=True)
    def test_constructor(self, Pool, Runner):
        """
        Constructor has to create correct state. Checking main variables
        """
        config = Mock(spec=Config)
        Runner.return_value = "runner"
        Pool.return_value = "proc pool"

        handler = FileChangeHandler(config=config)

        Pool.assert_called_once_with(1)
        self.assertEqual(handler._pool, "proc pool")
        self.assertEqual(handler.config, config)
        config.load_config.assert_called_once_with()
        Runner.assert_called_once_with()
        self.assertEqual(handler.test_runner, "runner")
        self.assertEqual(handler.pevent, handler.exclude_filter_wrapper)

    @patch.object(FileChangeHandler, "start_tests_async", autospec=True)
    @patch.object(FileChangeHandler, "show_notification", autospec=True)
    @patch.object(FileChangeHandler, "__init__", return_value=None)
    def test_task_done_early(self, init, show_notification, start_tests_async):
        """
        Test are done, nothing intersting happened since test started (+delay)
        """

        handler = FileChangeHandler()
        handler._last_event = 2
        handler._started = 1
        handler.delay = 5

        handler.task_done(("Result", "Info"))

        show_notification.assert_called_with(handler, "Result", "Info")
        self.assertFalse(start_tests_async.called)

    @patch.object(FileChangeHandler, "start_tests_async", autospec=True)
    @patch.object(FileChangeHandler, "show_notification", autospec=True)
    @patch.object(FileChangeHandler, "__init__", return_value=None)
    def test_task_done_run_next(self, init, notification, start_tests_async):
        """
        Test are done, something interesting happened since test started +delay
        """

        handler = FileChangeHandler()
        handler._last_event = 10
        handler._started = 2
        handler.delay = 5

        handler.task_done(("Result", "Info"))

        notification.assert_called_with(handler, "Result", "Info")
        start_tests_async.assert_called_once_with(handler)

    @patch("testrunner.watcher.pyinotify.WatchManager", autospec=True)
    @patch("testrunner.watcher.pyinotify.ThreadedNotifier", autospec=True)
    @patch("testrunner.watcher.FileChangeHandler", autospec=True)
    @patch("testrunner.watcher.Config", autospec=True)
    def test_main(self, config, f_c_handler, ThreadedNotifier, WatchManager):
        """
        Main entry point
        """

        WatchManager.return_value = "wm"
        config.return_value = "conf"
        f_c_handler.return_value = "handler"
        notifier = Mock()
        ThreadedNotifier.return_value = notifier

        watch()

        WatchManager.assert_called_once_with()
        config.assert_called_once_with(watch_manager="wm")
        f_c_handler.assert_called_once_with(config="conf")
        ThreadedNotifier.assert_called_once_with("wm", "handler")
        notifier.loop.assert_called_once_with()


@patch.object(FileChangeHandler, "__init__", return_value=None)
class TestFileChangeHandlerAsync(TestCase):

    def test_async_task_in_progress(self, init):
        """
        Trying to start a task while earlier task is not done yet
        """

        handler = FileChangeHandler()
        config = Mock(spec=Config)
        atask = Mock()
        atask.ready.return_value = False
        handler._atask = atask
        handler.config = config

        handler.start_tests_async()

        self.assertFalse(config.tests_command.called)

    @patch("testrunner.watcher.time", autospec=True)
    def test_async_task_started(self, time, init):
        """
        Trying to start a task while earlier task is not done yet
        """

        handler = FileChangeHandler()
        config = Mock(spec=Config)
        config.tests_command.side_effect = iter(["test-cmd", "suite-cmd"])
        atask = Mock()
        atask.ready.return_value = True
        pool = Mock()
        handler._atask = atask
        handler.config = config
        handler._pool = pool
        handler.test_runner = "test runner"
        time.return_value = 1

        handler.start_tests_async()

        config.tests_command.assert_has_calls([call(), call(suite=True)])
        pool.apply_async.assert_called_once_with(
            "test runner", ["test-cmd", "suite-cmd"],
            callback=handler.task_done
        )
        self.assertEqual(handler._started, 1)

    @patch("testrunner.watcher.time", autospec=True)
    def test_async_task_started_first_time(self, time, init):
        """
        Trying to start a task while earlier task is not done yet
        """

        handler = FileChangeHandler()
        config = Mock(spec=Config)
        config.tests_command.side_effect = iter(["test-cmd", "suite-cmd"])
        pool = Mock()
        handler._atask = None
        handler.config = config
        handler._pool = pool
        handler.test_runner = "test runner"
        time.return_value = 1

        handler.start_tests_async()

        config.tests_command.assert_has_calls([call(), call(suite=True)])
        pool.apply_async.assert_called_once_with(
            "test runner", ["test-cmd", "suite-cmd"],
            callback=handler.task_done
        )
        self.assertEqual(handler._started, 1)

    def test_filter_wrapper(self, init):
        """
        Calling filter function with event pathname
        """

        handler = FileChangeHandler()
        config = Mock(spec=Config)
        config.filter_wrapper.return_value = "filtered"
        handler.config = config
        event = Mock(spec=Event, pathname="file path")

        result = handler.exclude_filter_wrapper(event)

        self.assertEqual(result, "filtered")
        config.filter_wrapper.assert_called_once_with("file path")


@patch.object(FileChangeHandler, "start_tests_async", autospec=True)
@patch.object(FileChangeHandler, "__init__", return_value=None)
class TestFileChangeHandlerDefaultProcess(TestCase):

    @patch("testrunner.watcher.path", autospec=True)
    @patch("testrunner.watcher.time", autospec=True)
    def test_reloading_config(self, time, path, init, start_tests_async):
        """
        Event on local config file should trigger reload
        """

        handler = FileChangeHandler()
        handler.config = Mock(spec=Config)
        handler.config.config_file.return_value = "local conf path"
        event = Mock(spec=Event, pathname="conf path")
        time.return_value = 1
        path.exists.return_value = True
        path.samefile.return_value = True

        handler.process_default(event=event)

        path.exists.assert_has_calls([
            call("conf path"),
            call("local conf path"),
        ])
        path.samefile.assert_called_once_with("conf path", "local conf path")
        self.assertTrue(handler.config.load_config.called)

    @patch("testrunner.watcher.path", autospec=True)
    def test_config_deleted(self, path, init, start_tests_async):
        """
        Deleting local conf file does not trigger reloading
        """

        handler = FileChangeHandler()
        handler.config = Mock(spec=Config)
        handler.config.config_file.return_value = "local conf path"
        event = Mock(spec=Event, pathname="conf path")
        path.exists.return_value = False
        path.samefile.return_value = True

        handler.process_default(event=event)

        self.assertFalse(handler.config.load_config.called)

    @patch("testrunner.watcher.path", autospec=True)
    def test_event_on_non_config_file(self, path, init, start_tests_async):
        """
        Deleting local conf file does not trigger reloading
        """

        handler = FileChangeHandler()
        handler.config = Mock(spec=Config)
        handler.config.config_file.return_value = "local conf path"
        event = Mock(spec=Event, pathname="conf path")
        path.exists.return_value = True
        path.samefile.return_value = False

        handler.process_default(event=event)

        self.assertFalse(handler.config.load_config.called)

    @patch("testrunner.watcher.time", autospec=True)
    def test_run_test_on_event(self, time, init, start_tests_async):
        """
        Some file generated event
        """

        handler = FileChangeHandler()
        handler.config = Mock(spec=Config)
        event = Mock(spec=Event, pathname="conf path")
        time.return_value = 1

        handler.process_default(event=event)

        self.assertTrue(start_tests_async.called)
        self.assertEqual(handler._last_event, 1)


@patch("testrunner.watcher.pynotify.Notification", autospec=True)
@patch.object(FileChangeHandler, "__init__", return_value=None)
class TestFileChangeHandlerNotification(TestCase):

    def test_result_did_not_changed(self, init, Notification):
        handler = FileChangeHandler()
        handler.last_result = 1
        notification_obj = Mock()
        Notification.return_value = notification_obj

        handler.show_notification(1, "info")

        self.assertFalse(Notification.called)
        self.assertFalse(notification_obj.show.called)

    def test_show_notification_true(self, init, Notification):
        handler = FileChangeHandler()
        handler.last_result = False
        notification_obj = Mock()
        Notification.return_value = notification_obj

        handler.show_notification(True, "info")

        self.assertEqual(Notification.call_count, 1)
        call_args = Notification.call_args[0]
        self.assertIsInstance(call_args[0], basestring)
        self.assertEqual(call_args[1], "info")
        self.assertEqual(call_args[2], "dialog-info")
        self.assertTrue(notification_obj.show.called)

    def test_show_notification_false(self, init, Notification):
        handler = FileChangeHandler()
        handler.last_result = True
        notification_obj = Mock()
        Notification.return_value = notification_obj

        handler.show_notification(False, "info")

        self.assertEqual(Notification.call_count, 1)
        call_args = Notification.call_args[0]
        self.assertIsInstance(call_args[0], basestring)
        self.assertEqual(call_args[1], "info")
        self.assertEqual(call_args[2], "")
        self.assertTrue(notification_obj.show.called)
