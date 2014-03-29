Test Runner
==========
Simple Python module to run test when your code changes.

It can be used for TDD, modifying code will cause execution of tests

Installation
-----------

    pip install git+https://github.com/mrfuxi/testrunner.git

Basic Usage
-----------

    python -m testrunner

Features
--------

- Rerunning tests when code changes
- Rerunning tests when configuration file changes
- Runing test in 2 stages
    + Tests closely related to code you're working on atm
    + Remaining tests (all or wider subset)
- Notifications when tests changes state (Ubuntu atm)
- Changes to config applies to your tests on the next run (ie. what test to run)

Configuration
-------------

Command line options:

    python -m testrunner --help

By default module is looking for local config file in current directory.
This can be modified using command line option `-c`

Options in local config are the same as in testrunner.default_config
