import logging
import logging.config
from time import time
import imp
from os import path
from argparse import ArgumentParser

import pyinotify

from testrunner import default_config

logging.config.dictConfig(default_config.LOGGING)
_log = logging.getLogger(__name__)


class CommandLineConfig(object):  # pylint: disable=too-few-public-methods
    """
    Dummy class to store config from command line
    """
    pass


class Config(object):
    CONF_DEFAULT = 1
    CONF_LOCAL = 2
    CONF_COMMAND_LINE = 3

    filter_test = None

    def __init__(self, watch_manager, command_args=None):
        assert isinstance(watch_manager, pyinotify.WatchManager)

        self.config = None
        self.command_line = None

        self.config_loaded_at = None
        self.watcher_added_at = None

        self.watch_manager = watch_manager
        self.watch_descriptors = None

        self.parse_command_line(command_args)
        self.load_config()
        self.update_watch()

    def parse_command_line(self, command_args=None):
        parser = ArgumentParser(description="Automatic test runner for TDD")
        parser.add_argument("-r", help="Test runner", dest="runner")
        parser.add_argument("-c", help="Config file", dest="config")
        parser.add_argument("-d", help="Dir/file to watch", dest="dir")
        parser.add_argument("test", nargs="*", help="Tests to run")

        args = parser.parse_args(args=command_args)
        self.command_line = CommandLineConfig()

        parser_mapping = (
            ("runner", "TEST_RUNNER"),
            ("config", "CONFIG"),
            ("dir", "WATCH_DIR"),
            ("test", "TESTS"),
        )

        for cmd_name, conf_name in parser_mapping:
            cmd_val = getattr(args, cmd_name, None)
            if not cmd_val:
                continue

            setattr(self.command_line, conf_name, cmd_val)

        self.config_loaded_at = int(time())

    def load_config(self):
        if self.config and getattr(self.config, "CONFIG", None):
            del self.config.CONFIG
            _log.warning("Local config file can not specify it self, da!")

        config_file, source = self.get_value("CONFIG", source=True)

        _log.debug("Config file: %s", config_file)
        if not path.exists(config_file):
            message = "Config file {!r} does not exits".format(config_file)

            if source == self.CONF_COMMAND_LINE:
                raise ValueError(message)

            _log.info(message)
        else:
            module_name, ext = path.splitext(path.basename(config_file))
            if ext != ".py":
                raise ValueError("Config file is invalid. Python file excepted")

            module_path = path.dirname(config_file)
            module_info = imp.find_module(module_name, [module_path])
            self.config = imp.load_module("local_config", *module_info)
            _log.info("Config reloaded")

        self.config_loaded_at = int(time())
        self.update_watch()

    def get_value(self, name, source=False):
        order = (
            (self.command_line, self.CONF_COMMAND_LINE),
            (self.config, self.CONF_LOCAL),
            (default_config, self.CONF_DEFAULT),
        )

        for source_obj, source_id in order:
            try:
                value = getattr(source_obj, name)
            except AttributeError:
                pass
            else:
                if source:
                    return value, source_id

                return value

        raise ValueError("Config does not support {!r}".format(name))

    def get_values(self, names, source=False):
        return [self.get_value(name, source) for name in names]

    def tests_command(self, suite=False):
        params = ["TEST_RUNNER", "TEST_RUNNER_OPTIONS"]

        if not suite:
            params.extend(["TESTS_OPTIONS", "TESTS"])
        else:
            params.extend(["TEST_SUITE_OPTIONS", "TEST_SUITE"])

        conf_values = self.get_values(params)

        if conf_values[0] is None or conf_values[-1] is None:
            return None

        if isinstance(conf_values[-1], list):
            tests = conf_values.pop()
            conf_values.extend(tests)

        conf_values = filter(None, conf_values)

        test_cmd = " ".join(conf_values)
        _log.debug("Command to run: %s", test_cmd)
        return test_cmd

    def update_watch(self):
        if self.watcher_added_at >= self.config_loaded_at:
            _log.debug("Watcher up to date with config")
            return

        include = self.get_value("EVENTS_INCLUDE")
        exclude = self.get_value("EVENTS_EXCLUDE")
        watch = self.get_value("WATCH_DIR")
        exclude_filter = self.get_value("EXCLUDE_FILTER")
        conf_name = self.get_value("CONFIG")

        _log.debug("Dir to watch: %s", watch)
        _log.debug("Conf to watch: %s", conf_name)

        if isinstance(include, (list, tuple)):
            include = reduce(lambda x, y: x | y, include)

        if isinstance(exclude, (list, tuple)):
            exclude = reduce(lambda x, y: x | y, exclude)

        mask = include & ~exclude

        for descriptor in self.watch_descriptors or ():
            self.watch_manager.rm_watch(descriptor.values(),
                                        rec=True)

        if exclude_filter:
            self.filter_test = pyinotify.ExcludeFilter(exclude_filter)
        else:
            self.filter_test = None

        src_wd = self.watch_manager.add_watch(
            path=watch, mask=mask, auto_add=True,
            rec=True, exclude_filter=self.filter_wrapper)

        conf_wd = self.watch_manager.add_watch(path=conf_name, mask=mask)

        self.watcher_added_at = int(time())
        self.watch_descriptors = (src_wd, conf_wd)
        _log.info("Watcher updated")

    def config_file(self):
        """
        Returns location of local config
        """

        return self.get_value("CONFIG")

    def filter_wrapper(self, data):
        if self.filter_test is not None:
            return self.filter_test(data)

        return False
