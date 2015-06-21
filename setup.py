import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='humblematch',
    packages=['humblematch'],  # this must be the same as the name above
    version='0.1.dev3',
    description='Will Sanitize your type-checks and duck-checks for you',
    author='bendtherules',
    author_email='bendtherules@codesp.in',
    url='https://github.com/bendtherules/humblematch',  # use the URL to the github repo
    download_url='https://github.com/bendtherules/humblematch/tarball/0.1.dev3',  # I'll explain this in a second
    license='WTFPL',
    keywords=['type-checking', 'testing', 'assert'],  # arbitrary keywords
    classifiers=['Development Status :: 3 - Alpha', ],
    package_data={
        # Include all files in all packages
        # 'humblematch': ['docs/*.md', 'test/*'],
    },
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
