import operator

from django.template import Context, RequestContext, Template
from django.template.loader import select_template
from django.conf import settings

from shrubbery.utils.autodiscovery import autodiscover


class CachedProperty(object):
    def __init__(self, func, attr=None):
        self.func = func
        self.attr = attr or "_%s_cache" % func.__name__
        
    def __get__(self, instance, instance_type=None):
        if not hasattr(instance, self.attr):
            setattr(instance, self.attr, self.func())
        return getattr(instance, self.attr)
        
    def __set__(self, instance, value):
        setattr(instance, self.attr, value)
        
    def __delete__(self, instance):
        delattr(instance, self.attr)
        
def cached_property(arg):
    if isinstance(arg, str):
        def decorator(func):
            return CachedProperty(func, arg)
        return decorator
    else:
        return CachedProperty(arg)

class ClassProperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, cls):
        if instance:
            try:
                return instance.__dict__[self.getter.__name__]
            except KeyError:
                pass
        return self.getter(cls)

def class_property(func):
    return ClassProperty(func)


def force_iter(x):
    if isinstance(x, basestring):
        return iter((x,))
    try:
        return iter(x)
    except TypeError:
        return iter((x,))

def in_chunks_of(n, it, transpose=False):
    data = list(it)    
    if transpose:
        num = len(data) / n
        def run(offset):
            for i in xrange(offset, len(data), num):
                yield data[i]
        for offset in xrange(num):
            yield run(offset)
    else:
        def run(offset):
            for i in xrange(offset, min(len(data), offset + n)):
                yield data[i]
        for offset in xrange(0, len(data), n):
            yield run(offset)


def get_context(obj, request=None):
    if isinstance(obj, Context):
        return obj
    if obj is None:
        obj = {}
    if isinstance(obj, dict):
        if request:
            return RequestContext(request, obj)
        return Context(dict)            
    raise ValueError
    
def get_template(tpl):
    if isinstance(tpl, Template):
        return Template
    return select_template(*force_iter(tpl))
        
def reduce_and(x):
    return reduce(operator.__and__, x)
    
def reduce_or(x):
    return reduce(operator.__or__, x)
    
