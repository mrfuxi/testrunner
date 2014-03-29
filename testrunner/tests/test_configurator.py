from unittest import TestCase
from argparse import Namespace

from mock import MagicMock, Mock, patch, ANY, call
from pyinotify import WatchManager

from testrunner.configurator import Config
from testrunner import default_config


@patch.object(Config, "get_values", autospec=True)
@patch.object(Config, "__init__", return_value=None, autospec=True)
class TestConfigCmdRun(TestCase):

    def setUp(self):
        self.test_args = [
            "TEST_RUNNER", "TEST_RUNNER_OPTIONS",
            "TESTS_OPTIONS", "TESTS"
        ]

        self.suite_args = [
            "TEST_RUNNER", "TEST_RUNNER_OPTIONS",
            "TEST_SUITE_OPTIONS", "TEST_SUITE"
        ]

    def test_cmd_all_available(self, init, get_values):
        get_values.return_value = ["1", "2", "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, "1 2 3 4")

    def test_cmd_runner_options_missing(self, init, get_values):
        get_values.return_value = ["1", None, "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, "1 3 4")

    def test_cmd_options_missing(self, init, get_values):
        get_values.return_value = ["1", "2", None, "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, "1 2 4")

    def test_cmd_both_options_missing(self, init, get_values):
        get_values.return_value = ["1", None, None, "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, "1 4")

    def test_cmd_runner_missing(self, init, get_values):
        get_values.return_value = [None, "2", "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, None)

    def test_cmd_test_missing(self, init, get_values):
        get_values.return_value = ["1", "2", "3", None]
        conf = Config(None)
        cmd = conf.tests_command(suite=False)

        get_values.assert_called_with(conf, self.test_args)

        self.assertEqual(cmd, None)

    def test_cmd_suite_all_available(self, init, get_values):
        get_values.return_value = ["1", "2", "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, "1 2 3 4")

    def test_cmd_suite_runner_options_missing(self, init, get_values):
        get_values.return_value = ["1", None, "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, "1 3 4")

    def test_cmd_suite_options_missing(self, init, get_values):
        get_values.return_value = ["1", "2", None, "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, "1 2 4")

    def test_cmd_suite_both_options_missing(self, init, get_values):
        get_values.return_value = ["1", None, None, "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, "1 4")

    def test_cmd_suite_runner_missing(self, init, get_values):
        get_values.return_value = [None, "2", "3", "4"]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, None)

    def test_cmd_suite_missing(self, init, get_values):
        get_values.return_value = ["1", "2", "3", None]
        conf = Config(None)
        cmd = conf.tests_command(suite=True)

        get_values.assert_called_with(conf, self.suite_args)

        self.assertEqual(cmd, None)


class TestConfigOther(TestCase):
    """
    Some simple test cases
    """

    def test_constructor_watcher_type(self):
        """
        Type should be enforced
        """

        with self.assertRaises(AssertionError):
            Config(None)

    @patch.object(Config, "parse_command_line", autospec=True)
    @patch.object(Config, "load_config", autospec=True)
    @patch.object(Config, "update_watch", autospec=True)
    def test_constructor_setup(self, watch, load, parse):
        """
        Check initial setup
        """

        watch_manager = Mock(spec=WatchManager)
        conf = Config(watch_manager, command_args="args")

        parse.assert_called_once_with(conf, "args")
        load.assert_called_once_with(conf)
        watch.assert_called_once_with(conf)

    @patch.object(Config, "__init__", return_value=None, autospec=True)
    @patch.object(Config, "get_value", autospec=True)
    def test_config_file_location(self, get_value, init):
        """
        Getting location of config file
        """

        conf = Config(None)
        get_value.return_value = "test_conf.py"

        conf_file = conf.config_file()

        self.assertEqual(conf_file, "test_conf.py")
        get_value.assert_called_once_with(conf, "CONFIG")


@patch.object(Config, "__init__", return_value=None, autospec=True)
class TestConfigCommandLineParser(TestCase):

    @patch("testrunner.configurator.time")
    @patch("testrunner.configurator.ArgumentParser.parse_args")
    def test_override_existing(self, parse_args, mock_time, init):
        """
        Parsing command line should
        - override existing command line config
        - update time of last config change
        """

        mock_time.return_value = 1

        conf = Config(None)
        conf.command_line = "existing config"
        conf.parse_command_line()

        self.assertNotEqual(conf.command_line, "existing config")
        self.assertEqual(conf.config_loaded_at, 1)

    @patch("testrunner.configurator.ArgumentParser.parse_args")
    def test_parsing_empty_args(self, parse_args, init):
        """
        Result of empty args should be empty config dict
        """

        parse_args.return_value = MagicMock(spec=Namespace)

        conf = Config(None)
        conf.parse_command_line()
        self.assertEqual(conf.command_line.__dict__, {})

    @patch("testrunner.configurator.ArgumentParser.parse_args")
    def test_parsing_single_arg(self, parse_args, init):
        """
        Command line args get mapped to config dict
        """

        parser_mapping = (
            ("runner", "TEST_RUNNER"),
            ("config", "CONFIG"),
            ("dir", "WATCH_DIR"),
        )

        for arg_name, conf_name in parser_mapping:
            conf = Config(None)
            parsed = MagicMock(spec=Namespace, **{arg_name: arg_name})
            parse_args.return_value = parsed

            conf.parse_command_line()

            self.assertEqual(conf.command_line.__dict__, {conf_name: arg_name})

    @patch("testrunner.configurator.ArgumentParser.add_argument")
    @patch("testrunner.configurator.ArgumentParser.parse_args")
    def test_parsing_test_names(self, parse_args, add_argument, init):
        """
        Command line test args get mapped to config dict
        """

        conf = Config(None)
        parsed = MagicMock(test=[1, 2], spec=Namespace)
        parse_args.return_value = parsed

        conf.parse_command_line()

        add_argument.assert_any_call("test", nargs="*", help=ANY)
        self.assertEqual(conf.command_line.__dict__, {"TESTS": [1, 2]})


@patch.object(Config, "__init__", return_value=None, autospec=True)
class TestConfigGetValue(TestCase):

    def test_existing_value_default(self, init):
        conf = Config(None)
        conf.command_line = object()
        conf.config = object()

        value, source = conf.get_value("LOG_LEVEL", True)

        self.assertEqual(value, default_config.LOG_LEVEL)
        self.assertEqual(source, Config.CONF_DEFAULT)

    def test_existing_value_config(self, init):
        conf = Config(None)
        conf.command_line = object()
        conf.config = Mock(LOG_LEVEL="test value")

        value, source = conf.get_value("LOG_LEVEL", True)

        self.assertEqual(value, "test value")
        self.assertEqual(source, Config.CONF_LOCAL)

    def test_existing_value_command_line(self, init):
        conf = Config(None)
        conf.command_line = Mock(LOG_LEVEL="value form command line")
        conf.config = Mock(LOG_LEVEL="test value")

        value, source = conf.get_value("LOG_LEVEL", True)

        self.assertEqual(value, "value form command line")
        self.assertEqual(source, Config.CONF_COMMAND_LINE)

    def test_unexpected_value(self, init):
        conf = Config(None)
        conf.command_line = object()
        conf.config = object()

        with self.assertRaises(ValueError):
            conf.get_value("ABC", True)

    def test_value_source(self, init):
        conf = Config(None)
        conf.command_line = object()
        conf.config = object()

        values_source = conf.get_value("LOG_LEVEL", True)

        self.assertIsInstance(values_source, tuple)
        self.assertEqual(len(values_source), 2)

        value = conf.get_value("LOG_LEVEL", False)

        self.assertNotIsInstance(value, tuple)

    @patch.object(Config, "get_value", autospec=True)
    def test_get_values(self, get_value, init):
        conf = Config(None)
        get_value.side_effect = (x for x in range(3))

        values = conf.get_values(["a", "b", "c"])

        self.assertEqual(get_value.call_count, 3)
        self.assertEqual(values, [0, 1, 2])
        get_value.assert_has_calls([call(conf, x, False) for x in "abc"])

    @patch.object(Config, "get_value", autospec=True)
    def test_get_values_with_source(self, get_value, init):
        conf = Config(None)
        get_value.side_effect = ((x, "source") for x in range(3))

        values = conf.get_values(["a", "b", "c"], True)

        self.assertEqual(get_value.call_count, 3)
        self.assertEqual(values, [(0, "source"), (1, "source"), (2, "source")])
        get_value.assert_has_calls([call(conf, x, True) for x in "abc"])


@patch.object(Config, "__init__", return_value=None, autospec=True)
class TestConfigFilterWrapper(TestCase):

    def test_fitler_wrapper_corrent(self, init):
        """
        Test behaviour of wrapper given correct method
        """

        conf = Config(None)
        external_filter_test = Mock(return_value="X")
        conf.filter_test = external_filter_test

        result = conf.filter_wrapper("123")

        self.assertEqual(result, "X")
        external_filter_test.assert_called_once_with("123")

    def test_fitler_wrapper_none(self, init):
        """
        Test behaviour of wrapper without filter method
        """

        conf = Config(None)
        conf.filter_test = None

        result = conf.filter_wrapper("123")

        self.assertEqual(result, False)

    def test_fitler_wrapper_not_callable(self, init):
        """
        Test behaviour of wrapper without filter method
        """

        conf = Config(None)
        conf.filter_test = "test"

        with self.assertRaises(TypeError):
            conf.filter_wrapper("123")


@patch.object(Config, "__init__", return_value=None, autospec=True)
@patch.object(Config, "get_value", autospec=True)
@patch.object(Config, "update_watch", autospec=True)
class TestConfigLoading(TestCase):

    @patch("testrunner.configurator._log")
    @patch("testrunner.configurator.time")
    def test_config_defines_it_self(
            self, mock_time, log, update_watch, get_value, init):
        """
        Local config should not define location to another config...
        """

        conf = Config(None)
        conf.config = Mock(CONFIG="config.py")
        conf.config_loaded_at = 123
        get_value.return_value = ("aaa", "1")
        mock_time.return_value = 321

        conf.load_config()

        self.assertTrue(log.warning.called)

        with self.assertRaises(AttributeError):
            # CONFIG attribute should be deleted at this point
            conf.config.CONFIG

        self.assertEqual(conf.config_loaded_at, 321)
        self.assertTrue(update_watch.called)

    @patch("testrunner.configurator.path.exists")
    @patch("testrunner.configurator.time")
    def test_config_file_does_not_exit_default(
            self, mock_time, exists, update_watch, get_value, init):
        """
        Config file does not exit, specified in defaults
        """

        conf = Config(None)
        conf.config = None
        conf.config_loaded_at = 123
        get_value.return_value = ("file.py", conf.CONF_DEFAULT)
        exists.return_value = False
        mock_time.return_value = 321

        # not exception is raised now
        conf.load_config()

        exists.assert_called_with("file.py")
        self.assertEqual(conf.config_loaded_at, 321)
        self.assertTrue(update_watch.called)

    @patch("testrunner.configurator.path.exists")
    def test_config_file_does_not_exit_command_line(
            self, exists, update_watch, get_value, init):
        """
        Config file does not exit, specified in command line args
        """

        conf = Config(None)
        conf.config = None
        conf.config_loaded_at = 123
        get_value.return_value = ("file.py", conf.CONF_COMMAND_LINE)
        exists.return_value = False

        with self.assertRaises(ValueError):
            conf.load_config()

        exists.assert_called_with("file.py")
        self.assertEqual(conf.config_loaded_at, 123)
        self.assertFalse(update_watch.called)

    @patch("testrunner.configurator.path.exists")
    @patch("testrunner.configurator.time")
    @patch("testrunner.configurator.imp.find_module")
    @patch("testrunner.configurator.imp.load_module")
    def test_config_file_exits_command_line(
            self, load_mod, find_mod, mock_time,
            exists, update_watch, get_value, init):
        """
        Config file does not exit, specified in command line args
        """

        conf = Config(None)
        conf.config = None
        conf.config_loaded_at = 123
        get_value.return_value = ("test/file.py", "source")
        exists.return_value = True
        mock_time.return_value = 321
        find_mod.return_value = ["val_1", "val_2"]

        conf.load_config()

        exists.assert_called_with("test/file.py")

        find_mod.assert_called_with("file", ["test"])
        load_mod.assert_called_with("local_config", "val_1", "val_2")

        self.assertEqual(conf.config_loaded_at, 321)
        self.assertTrue(update_watch.called)

    @patch("testrunner.configurator.path.exists")
    def test_config_file_exits_command_line_wrong_ext(
            self, exists, update_watch, get_value, init):
        """
        Config file does not exit, specified in command line args
        """

        conf = Config(None)
        conf.config = None
        conf.config_loaded_at = 123
        get_value.return_value = ("file.txt", "source")
        exists.return_value = True

        with self.assertRaises(ValueError):
            conf.load_config()

        exists.assert_called_with("file.txt")
        self.assertEqual(conf.config_loaded_at, 123)
        self.assertFalse(update_watch.called)


@patch.object(Config, "__init__", return_value=None, autospec=True)
@patch.object(Config, "get_value", autospec=True)
class TestConfigUpdatingWatcher(TestCase):
    def _helper(self):
        conf = Config(None)
        conf.watcher_added_at = 1
        conf.config_loaded_at = 2
        conf.watch_descriptors = None
        conf.watch_manager = Mock()

        self.conf = conf

    def test_too_early_to_update(self, get_value, init):
        """
        It should be safe to call update watch at any point,
        however action should be executed only when needed
        """
        self._helper()
        self.conf.watcher_added_at = 2
        self.conf.config_loaded_at = 1

        self.conf.update_watch()

        # Early return, no values should be accessed
        self.assertFalse(get_value.called)

    def test_no_watch_decriptor(self, get_value, init):
        """
        When descriptor does not exits yet, do not try to remove it
        """
        self._helper()
        get_value.side_effect = iter([1, 4, "dir", None, "config"])

        self.conf.update_watch()

        self.assertFalse(self.conf.watch_manager.rm_watch.called)

    # @expectedFailure
    def test_watch_decriptor_present(self, get_value, init):
        """
        When descriptor does not exits yet, do not try to remove it
        """
        self._helper()
        src_descriptor = Mock()
        src_descriptor.values.return_value = "src_descr"
        conf_descriptor = Mock()
        conf_descriptor.values.return_value = "conf_descr"
        self.conf.watch_descriptors = [src_descriptor, conf_descriptor]
        get_value.side_effect = iter([1, 4, "dir", None, "config"])

        self.conf.update_watch()

        self.conf.watch_manager.rm_watch.assert_has_calls([
            call("src_descr", rec=True),
            call("conf_descr", rec=True),
        ])

    @patch("testrunner.configurator.pyinotify.ExcludeFilter")
    def test_filter_present(self, in_filter, get_value, init):
        """
        Test applying filters
        """

        self._helper()
        get_value.side_effect = iter([1, 4, "dir", "filters", "config"])
        self.conf.filter_test = "some function"
        in_filter.return_value = "new function"

        self.conf.update_watch()

        in_filter.assert_called_once_with("filters")
        self.assertEqual(self.conf.filter_test, "new function")

    @patch("testrunner.configurator.pyinotify.ExcludeFilter")
    def test_filters_not_set(self, in_filter, get_value, init):
        """
        Test filters not set
        """

        self._helper()
        get_value.side_effect = iter([1, 4, "dir", [], "config"])
        self.conf.filter_test = "some function"
        in_filter.return_value = "new function"

        self.conf.update_watch()

        self.assertFalse(in_filter.called)
        self.assertEqual(self.conf.filter_test, None)

    @patch("testrunner.configurator.time")
    def test_set_new_watch(self, mock_time, get_value, init):
        """
        Setting new watch for dir
        """
        self._helper()
        self.conf.watcher_added_at = 1
        add_watch = Mock()
        add_watch.side_effect = iter(["dir descriptor", "conf descriptor"])
        self.conf.watch_manager.add_watch = add_watch
        get_value.side_effect = iter([1, 2, "dir", None, "config"])
        mock_time.return_value = 2

        self.conf.update_watch()

        self.assertEqual(add_watch.call_count, 2)
        add_watch.assert_has_calls([
            call(path="dir", mask=1 & ~2, auto_add=True,
                 rec=True, exclude_filter=self.conf.filter_wrapper),
            call(path="config", mask=1 & ~2),
        ])
        self.assertEqual(
            self.conf.watch_descriptors, ("dir descriptor", "conf descriptor"))
        self.assertEqual(self.conf.watcher_added_at, 2)

    @patch("testrunner.configurator.time")
    def test_include_excelude_list(self, mock_time, get_value, init):
        """
        Include/exclude should accept a list of flags
        """
        self._helper()
        self.conf.watcher_added_at = 1
        add_watch = Mock()
        add_watch.side_effect = iter(["src descr", "conf descr"])
        self.conf.watch_manager.add_watch = add_watch

        filter_include = [1, 4094]
        filter_exclude = [8, 16, 32]
        get_value.side_effect = iter([
            filter_include, filter_exclude, "dir", None, "config"
        ])

        ored_include = 4095
        ored_exclude = 56
        expected_mask = ored_include & ~ored_exclude

        mock_time.return_value = 2

        self.conf.update_watch()

        self.assertEqual(add_watch.call_count, 2)
        add_watch.assert_has_calls([
            call(path="dir", mask=expected_mask, auto_add=True,
                 rec=True, exclude_filter=self.conf.filter_wrapper),
            call(path="config", mask=expected_mask),
        ])
        self.assertEqual(
            self.conf.watch_descriptors, ("src descr", "conf descr"))
        self.assertEqual(self.conf.watcher_added_at, 2)

    @patch("testrunner.configurator.time")
    def test_include_excelude_tuple(self, mock_time, get_value, init):
        """
        Include/exclude should accept a tuple of flags
        """
        self._helper()
        self.conf.watcher_added_at = 1
        add_watch = Mock()
        add_watch.side_effect = iter(["src descr", "conf descr"])
        self.conf.watch_manager.add_watch = add_watch

        filter_include = (1, 4094)
        filter_exclude = (8, 16, 32)
        get_value.side_effect = iter([
            filter_include, filter_exclude, "dir", None, "config"
        ])

        ored_include = 4095
        ored_exclude = 56
        expected_mask = ored_include & ~ored_exclude

        mock_time.return_value = 2

        self.conf.update_watch()

        self.assertEqual(add_watch.call_count, 2)
        add_watch.assert_has_calls([
            call(path="dir", mask=expected_mask, auto_add=True,
                 rec=True, exclude_filter=self.conf.filter_wrapper),
            call(path="config", mask=expected_mask),
        ])
        self.assertEqual(
            self.conf.watch_descriptors, ("src descr", "conf descr"))
        self.assertEqual(self.conf.watcher_added_at, 2)
