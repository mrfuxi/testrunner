import sys
from unittest import TestCase
from mock import Mock, patch, ANY, call

import pexpect

from testrunner.runner import Runner


@patch("testrunner.runner.pexpect.spawnu", autospec=True)
class TestRunner(TestCase):
    def setUp(self):
        self.runner = Runner()

    def test_expected_console_outputs(self, spawnu=None):
        """
        Script should do stuff for EOF or when debugger is triggered
        """

        self.assertIn(pexpect.EOF, self.runner._excepted)
        self.assertIn("pdb", repr(self.runner._excepted).lower())

    def test_spawning_pocesses_clean_exit(self, spawnu):
        """
        Running simple command that succeeds - no tracking
        """

        proc = Mock(logfile=None, exitstatus=0)
        proc.expect.return_value = 0
        spawnu.return_value = proc

        result = self.runner.run_test("test-cmd", progress=False)

        spawnu.assert_called_once_with("test-cmd")
        self.assertEqual(proc.logfile, None)
        proc.expect.assert_called_once_with(self.runner._excepted, timeout=ANY)
        self.assertTrue(proc.close.called)
        self.assertTrue(result)

    def test_spawning_pocesses_clean_exit_progess(self, spawnu):
        """
        Running simple command that succeeds - with tracking
        """

        proc = Mock(logfile=None, exitstatus=0)
        proc.expect.return_value = 0
        spawnu.return_value = proc

        result = self.runner.run_test("test-cmd", progress=True)

        spawnu.assert_called_once_with("test-cmd")
        self.assertEqual(proc.logfile, sys.stderr)
        proc.expect.assert_called_once_with(self.runner._excepted, timeout=ANY)
        self.assertTrue(proc.close.called)
        self.assertTrue(result)

    @patch("testrunner.runner._log", autospec=True)
    def test_spawning_pocesses_errors(self, logger, spawnu):
        """
        Running simple command that exits with an error
        """
        proc = Mock(logfile=None, exitstatus=1, before="error message")
        proc.expect.return_value = 0
        spawnu.return_value = proc

        result = self.runner.run_test("test-cmd", progress=False)

        spawnu.assert_called_once_with("test-cmd")
        self.assertEqual(proc.logfile, None)
        proc.expect.assert_called_once_with(self.runner._excepted, timeout=ANY)
        self.assertTrue(proc.close.called)
        self.assertIn("error message", repr(logger.error.call_args))
        self.assertFalse(result)

    @patch("testrunner.runner._log", autospec=True)
    def test_spawning_pocesses_with_debugger(self, logger, spawnu):
        """
        Running simple command interrupted with debugger
        """

        proc = Mock(logfile=None, exitstatus=0, before="msg")
        proc.expect.return_value = 1
        spawnu.return_value = proc

        result = self.runner.run_test("test-cmd", progress=False)

        spawnu.assert_called_once_with("test-cmd")
        self.assertIn("msg", repr(logger.info.call_args))
        proc.sendline.assert_called_once_with("")
        proc.interact.assert_called_once_with()
        self.assertEqual(proc.logfile, None)
        proc.expect.assert_called_once_with(self.runner._excepted, timeout=ANY)
        self.assertTrue(proc.close.called)
        self.assertTrue(result)


@patch.object(Runner, "run_test", autospec=True)
class TestRunnerCall(TestCase):

    def test_main_test_failure(self, run_test):
        """
        Command (test) fails, no extra code is executed
        """
        run_test.return_value = False
        runner = Runner()

        result, msg = runner("test-cmd", suite_cmd=None)

        self.assertFalse(result)
        self.assertIsInstance(msg, basestring)
        run_test.assert_called_once_with(runner, "test-cmd", progress=ANY)

    def test_main_ok_no_suite(self, run_test):
        """
        Command (test) succeeds, no suite to run
        """
        run_test.return_value = True
        runner = Runner()

        result, msg = runner("test-cmd", suite_cmd=None)

        self.assertTrue(result)
        self.assertIsInstance(msg, basestring)
        run_test.assert_called_once_with(runner, "test-cmd", progress=ANY)

    def test_main_ok_suite_fails(self, run_test):
        """
        Command (test) succeeds, suite fails
        """
        run_test.side_effect = iter([True, False])
        runner = Runner()

        result, msg = runner("test-cmd", suite_cmd="suite-cmd")

        self.assertFalse(result)
        self.assertIsInstance(msg, basestring)
        run_test.assert_has_calls([
            call(runner, "test-cmd", progress=ANY),
            call(runner, "suite-cmd"),
        ])
        self.assertEqual(run_test.call_count, 2)

    def test_main_ok_suite_ok(self, run_test):
        """
        Command (test) and suite succeeds
        """
        run_test.return_value = True
        runner = Runner()

        result, msg = runner("test-cmd", suite_cmd="suite-cmd")

        self.assertTrue(result)
        self.assertIsInstance(msg, basestring)
        run_test.assert_has_calls([
            call(runner, "test-cmd", progress=ANY),
            call(runner, "suite-cmd"),
        ])
        self.assertEqual(run_test.call_count, 2)
