#
# build the source distribution for tor_async_couchdb-*.*.*.tar.gz
#
#   >git clone https://github.com/simonsdave/tor-async-couchdb.git
#   >cd tor-async-couchdb
#   >source cfg4dev
#   >python setup.py sdist --formats=gztar
#
# update pypitest with both meta data and source distribution (FYI ...
# use of pandoc is as per https://github.com/pypa/pypi-legacy/issues/148#issuecomment-226939424
# since PyPI requires long description in RST but the repo's readme is in
# markdown)
#
#   >pandoc README.md -o README.rst
#   >python setup.py register -r pypitest
#   >twine upload dist/* -r pypitest
#
# use the package uploaded to pypitest
#
#   >pip install -i https://testpypi.python.org/pypi tor_async_couchdb
#
import re
import sys
from setuptools import setup

#
# this approach used below to determine ```version``` was inspired by
# https://github.com/kennethreitz/requests/blob/master/setup.py#L31
#
# why this complexity? wanted version number to be available in the
# a runtime.
#
# the code below assumes the distribution is being built with the
# current directory being the directory in which setup.py is stored
# which should be totally fine 99.9% of the time. not going to add
# the coode complexity to deal with other scenarios
#
reg_ex_pattern = r"__version__\s*=\s*['\"](?P<version>[^'\"]*)['\"]"
reg_ex = re.compile(reg_ex_pattern)
version = ""
with open("tor_async_couchdb/__init__.py", "r") as fd:
    for line in fd:
        match = reg_ex.match(line)
        if match:
            version = match.group("version")
            break
if not version:
    raise Exception("Can't locate tor_async_couchdb's version number")

_download_url = "https://github.com/simonsdave/tor-async-couchdb/tarball/v%s" % version


def _long_description():
    """Assuming the following command is used to register the package
        python setup.py register -r pypitest
    then sys.argv should be
        ['setup.py', 'register', '-r', 'pypitest']
    """
    if 2 <= len(sys.argv) and sys.argv[1] == 'register':
        with open('README.rst', 'r') as f:
            return f.read()

    return 'a long description'


# list of valid classifiers @ https://pypi.python.org/pypi?%3Aaction=list_classifiers
_classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

_author = "Dave Simons"
_author_email = "simonsdave@gmail.com"

_keywords = [
    'tornado',
    'couchdb',
]

setup(
    name="tor_async_couchdb",
    packages=[
        "tor_async_couchdb",
    ],
    install_requires=[
        "python-keyczar==0.716",
        "requests>=2.7.0",
    ],
    version=version,
    description="Tornado Async Client for CouchDB",
    long_description=_long_description(),
    author=_author,
    author_email=_author_email,
    maintainer=_author,
    maintainer_email=_author_email,
    license="MIT",
    url="https://github.com/simonsdave/tor-async-couchdb",
    download_url=_download_url,
    keywords=_keywords,
    classifiers=_classifiers,
)
