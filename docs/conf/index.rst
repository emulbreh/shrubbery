.. module:: shrubbery.db

.. _conf:

==============
shrubbery.conf
==============

Overview
~~~~~~~~
Provides utilities for app-local settings::

    from shrubbery.conf import settings
    
    # it proxies attribute access to django.conf.settings
    settings.DEBUG
    
    # app specific settings are available through `settings` ..
    settings['shrubbery.polymorph'].OBJECT_IDENTITY_DB_TABLE
    
    # .. or via direct import
    from shrubbery.polymorph.conf import settings
    

Providing app-local settings::

    from shrubbery import conf

    class settings(conf.Settings):
        FOO = conf.Setting()
        BAR = conf.Setting(default='bar')

.. class:: Settings:


Settings
========

