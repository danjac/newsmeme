# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~~~~~

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

"""
newsmeme
--------

"""
from setuptools import setup

setup(
    name='newsmeme',
    version='0.1',
    url='<enter URL here>',
    license='BSD',
    author='Dan Jacob',
    author_email='your-email-here@example.com',
    description='<enter short description here>',
    long_description=__doc__,
    packages=['newsmeme'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Flask-Cache',
        'Flask-SQLAlchemy',
        'Flask-Principal',
        'Flask-WTF',
        'Flask-Mail',
        'Flask-Testing',
        'Flask-Script',
        'Flask-OpenID',
        'Flask-Babel',
        'Flask-Themes',
        'sqlalchemy',
        'markdown',
        'feedparser',
        'blinker',
        'nose',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
