import imp
from django.utils.importlib import import_module
from django.conf import settings
   
def autodiscover(module_name):    
    modules = {}
    for app in settings.INSTALLED_APPS:
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue
        try:
            imp.find_module(module_name, app_path)
        except ImportError:
            continue
        modules[app] = import_module("%s.%s" % (app, module_name))
    return modules