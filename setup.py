# -*- coding: utf-8 -*-
import os.path
import re
import warnings
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.1'

news = os.path.join(os.path.dirname(__file__), 'docs', 'news.rst')
news = open(news).read()
parts = re.split(r'([0-9\.]+)\s*\n\r?-+\n\r?', news)
found_news = ''
for i in range(len(parts)-1):
    if parts[i] == version:
        found_news = parts[i+i]
        break
if not found_news:
    warnings.warn('No news for this version found.')

long_description = """
This is a utility to get rides from Garmin Connect and upload them to Strava.
"""

if found_news:
    title = 'Changes in %s' % version
    long_description += "\n%s\n%s\n" % (title, '-'*len(title))
    long_description += found_news 

setup( 
    name = "connectstrava", 
    version = version, 
    author = "Hans Lellelid", 
    author_email = "hans@xmpl.org",
    url = "http://github.com/hozn/connectstrava",
    license = "Apache",
    description = "Simple utility to sync rides from Garmin Connect to Strava.",
    long_description = long_description,
    packages = find_packages(),
    include_package_data=True,
    package_data={'connectstrava': ['tests/resources/*']},
    install_requires=['python-dateutil{0}'.format('>=2.0,<3.0dev' if sys.version_info[0] == 3 else '>=1.5,<2.0dev'), # version 1.x is for python 2 and version 2.x is for python 3.
                      'pytz',
                      'requests>=1.1.0,<2.0dev',
                      'beautifulsoup4>=4.0,<5.0dev',
                      'stravalib'],
    tests_require = ['nose>=1.0.3'],
    test_suite = 'connectstrava.tests',
    classifiers=[
       'Development Status :: 3 - Alpha',
       'License :: OSI Approved :: Apache Software License',
       'Intended Audience :: Developers',
       'Operating System :: OS Independent',
       'Programming Language :: Python :: 2.6',
       'Programming Language :: Python :: 2.7',
       'Programming Language :: Python :: 3.0',
       'Programming Language :: Python :: 3.1',
       'Programming Language :: Python :: 3.2',
       'Programming Language :: Python :: 3.3',
       "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points="""
    [console_scripts]
    connect-init-db=connectstrava.cli:init_db
    connect-sync-rides=connectstrava.cli:sync_rides
    """,
    use_2to3=True,
    zip_safe=False # Technically it should be fine, but there are issues w/ 2to3 
)
