import logging
import sys

import pexpect

_log = logging.getLogger(__name__)


class Runner(object):
    def __init__(self):
        self._excepted = [pexpect.EOF, u"ipdb>", u"(Pdb)"]
        self.last_traceback = ""

    def run_test(self, test_cmd, progress=False):
        _log.debug("To run: %s", test_cmd)

        self.last_traceback = ""
        proc = pexpect.spawnu(test_cmd)

        if progress:
            proc.logfile = sys.stderr

        state = proc.expect(self._excepted, timeout=5)

        if state != 0:
            _log.info(proc.before.rstrip("\r\n"))
            proc.sendline("")
            proc.interact()

        proc.close()

        test_result = proc.exitstatus == 0

        if not test_result:
            self.last_traceback = proc.before
            _log.error(u"\n{}".format(proc.before))

        return test_result

    def __call__(self, test_cmd, suite_cmd=None):
        if not self.run_test(test_cmd, progress=False):
            msg = "Tests failed"
            _log.error(msg)
            return False, msg

        msg = u"Tests are fine \u263A"
        _log.info(msg)

        if not suite_cmd:
            return True, msg

        if not self.run_test(suite_cmd):
            msg = u"Test suite failed"
            _log.error(msg)
            return False, msg

        _log.info(u"Test suite run fine too \u263A")

        return True, u"All tests are fine \u263A"
