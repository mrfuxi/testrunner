from distutils.core import setup

setup(
    name="testrunner",
    version="0.1",
    author="Karol Duleba",
    author_email="mr.fuxi@gmail.com",
    url="https://github.com/mrfuxi/testrunner",
    license="MIT",
    description="Test runner for TDD",
    long_description=open("README.md").read(),
    packages=["testrunner"],
    install_requires=[
        "nose-notify == 0.4.2",
        "pexpect == 3.1",
        "pyinotify == 0.9.4",
    ],
)
