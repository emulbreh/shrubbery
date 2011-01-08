#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='django-shrubbery',
    version='1.0.0',
    description='Misc utilities for django.',
    author='Johannes Dollinger',
    author_email='emulbreh@e6h.de',
    url='http://code.e6h.de/shrubbery/',
    packages=[
        'shrubbery',
        'shrubbery.db',
        'shrubbery.polymorph',
        'shrubbery.tagging',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)