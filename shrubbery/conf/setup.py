import os
import inspect

from shrubbery.conf.base import app_settings

__all__ = ['app']

def app(name, settings=None):
    if settings:
        app_settings[name] = settings
    return name

