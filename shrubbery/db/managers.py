from django.db import models
from django.db.models.query import QuerySet

from shrubbery.db.utils import fetch

def _create_proxy_method(name):
    def proxy(self, *args, **kwargs):
        return getattr(self.get_query_set(), name)(*args, **kwargs)
    return proxy


class ManagerBase(type):
    def __new__(cls, name, bases, attrs):
        meta = attrs.pop('Meta', None)
        new_cls = super(ManagerBase, cls).__new__(cls, name, bases, attrs)
        queryset_cls = getattr(meta, 'queryset', None)
        if queryset_cls:
            if isinstance(queryset_cls, tuple):
                queryset_cls = type('_'.join([cls.__name__ for cls in queryset_cls]), queryset_cls, {})
            if queryset_cls:
                new_cls._queryset_cls = queryset_cls
                for name, attr in queryset_cls.__dict__.items():
                    if callable(attr) and getattr(attr, '_manager_proxy_method', False):
                        setattr(new_cls, name, _create_proxy_method(name))
        else:
            if not hasattr(new_cls, '_queryset_cls'):
                new_cls._queryset_cls = QuerySet
        return new_cls


_queryset_manager_cache = {}

class Manager(models.Manager):
    __metaclass__ = ManagerBase

    def get_query_set(self):
        if not self._queryset_cls:
            return super(Manager, self).get_query_set()
        return self._queryset_cls(self.model)

    @staticmethod
    def proxy_method(method):
        method._manager_proxy_method = True
        return method

    @classmethod
    def for_queryset(cls, queryset_cls):
        key = (cls, queryset_cls)
        if key not in _queryset_manager_cache:
            manager_cls = type("%sManager" % queryset_cls.__name__.replace('QuerySet', ''), (cls,), {
                '__module__': queryset_cls.__module__,
                'Meta': type('Meta', (object,), {
                    'queryset': queryset_cls
                })
            })
            _queryset_manager_cache[key] = manager_cls
        return _queryset_manager_cache[key]


class QuerySetPlus(models.query.QuerySet):
    @Manager.proxy_method
    def filter(self, *args, **kwargs):
        if args and hasattr(args[0], 'add_to_query'):
            return self.complex_filter(*args)
        return super(QuerySetPlus, self).filter(*args, **kwargs)

    @Manager.proxy_method
    def exclude(self, *args, **kwargs):
        if args and hasattr(args[0], 'add_to_query'):
            try:
                q = ~args[0]
            except TypeError:
                raise TypeError('QuerySetPlus.exclude() requires a ')
            return self.complex_filter(q)
        return super(QuerySetPlus, self).exclude(*args, **kwargs)

    @Manager.proxy_method
    def fetch(self, *args):
        return fetch(self, *args)
