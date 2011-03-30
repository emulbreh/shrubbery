from django.core.urlresolvers import reverse as django_reverse
from django.utils.importlib import import_module
from django.db.models import Model
from django.conf import settings
from django.http import HttpResponseRedirect

from shrubbery.utils import force_iter, autodiscovery

class NoUrlMapping(Exception):
    def __init__(self, obj, use_case):
        self.obj = obj
        self.use_case = use_case

    def __str__(self):
        return "%r use-case=%s" % (self.obj, self.use_case)
        

class UrlMap(object):
    def __init__(self):
        self.registry = {}
        self.default_mappers = {}
        self.instance_registry = {}
        
    def register(self, subject, view=None, defaults=None, mapper=None, use_case=(None,), instances=True):
        if view:            
            if not defaults:
                defaults = {}
            if instances:
                reg = self.registry
            else:
                reg = self.instance_registry                
            for uc in force_iter(use_case):
                reg[(subject, uc)] = (view, defaults, mapper)
        else:
            def decorator(func):
                self.register(subject, func, defaults=defaults, use_case=use_case, instance=instance, mapper=mapper)
                return func
            return decorator
            
    def include(self, urlmap):
        if isinstance(urlmap, str):
            urlmap = import_module(urlmap).urlmap
        if isinstance(urlmap, UrlMap):
            self.registry.update(urlmap.registry)
            self.instance_registry.update(urlmap.instance_registry)
            self.default_mappers.update(urlmap.default_mappers)
        else:
            raise ValueError

    def get_view(self, obj, use_case):
        try:
            return self.instance_registry[(obj, use_case)]
        except KeyError:
            pass
        for subject in obj.__class__.mro():
            try:
                return self.registry[(subject, use_case)]
            except KeyError:
                pass
        raise KeyError
        
    def get_default_mapper(self, obj, use_case=None):
        for subject in obj.__class__.mro():
            try:
                return self.default_mappers[(subject, use_case)]
            except KeyError:
                try:
                    return self.default_mappers[(subject, None)]
                except KeyError:
                    pass
        return None
        
    def set_default_mapper(self, obj_type, mapper, use_case=(None,)):
        for uc in force_iter(use_case):
            self.default_mappers[(obj_type, uc)] = mapper
        
    def reverse(self, obj, use_case=None, kwargs=None):
        try:
            view, defaults, mapper = self.get_view(obj, use_case)
        except KeyError:
            if not use_case and hasattr(obj, 'get_absolute_url'):
                return obj.get_absolute_url()
            else:
                raise NoUrlMapping(obj, use_case)
        else:
            if not mapper:
                mapper = self.get_default_mapper(obj, use_case)
        # defaults < mapper < kwargs
        if mapper:
            obj_kwargs = mapper(obj)
        else:
            obj_kwargs = {}
        for name, value in defaults:
            obj_kwargs.setdefault(name, value)
        if kwargs:
            obj_kwargs.update(kwargs)
        return django_reverse(view, kwargs=obj_kwargs)
    
    def redirect_to(self, obj, use_case=None, kwargs=None):
        return HttpResponseRedirect(self.reverse(obj, use_case, args, kwargs))
        
    def autodiscover(self):
        for app, module in autodiscovery.autodiscover('urlmap').items():
            self.include(module.urlmap)

_root_urlmap = UrlMap()
_root_urlmap.set_default_mapper(Model, lambda obj: {'pk': obj.pk}, use_case=[None, 'details', 'update', 'delete'])

def get_root_urlmap():
    if not getattr(_root_urlmap, '_loaded', False):
        if hasattr(settings, 'ROOT_URLMAP'):
            _root_urlmap.include(settings.ROOT_URLMAP)
        else:
            _root_urlmap.autodiscover()
        _root_urlmap._loaded = True
    return _root_urlmap

def reverse(obj, kwargs=None, use_case=None):
    urlmap = get_root_urlmap()
    return urlmap.reverse(obj, kwargs=kwargs, use_case=use_case)
    
def redirect_to(obj, kwargs=None, use_case=None):
    urlmap = get_root_urlmap()
    return urlmap.redirect_to(obj, kwargs=kwargs, use_case=use_case)
    