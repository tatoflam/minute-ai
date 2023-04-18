from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

def parse_requirements(filename):
    """ Given a filename, strip empty lines and those beginning with # """
    output = []
    with open(filename, 'r') as f:
        for line in f:
            sline = line.strip()
            if sline and not line.startswith('#'):
                output.append(sline)
    return output

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name="minutes",
    version="1.0",
    url="https://github.com/tatoflam/minutes-ai",
    author="tatoflam",
    author_email="tatsuro@hommalab.io",
    license="MIT",
    packages=find_packages(),
    cmdclass={"test": PyTest},
    # install_requires=parse_requirements("requirements.txt"),
    # tests_require=parse_requirements("requirements.testing.txt"),
    description="Transcribes audio spoken in any language \
        Outputs a summary of that language and any translated language in markdown format",
    # long_description="\n" + get_readme()
)