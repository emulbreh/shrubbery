from django.db import models

from shrubbery.db.utils import fetch

class QuerySet(models.query.QuerySet):
    def prepare_filter_kwargs(self, kwargs):
        for name, value in kwargs.items():
            if name.endswith('__in') and isinstance(value, QuerySet):
                kwargs[name] = value.values('pk').query
        return kwargs

    @Manager.proxy_method
    def filter(self, *args, **kwargs):
        if len(args) == 1 and hasattr(args[0], 'add_to_query'):
            return self.complex_filter(*args)
        kwargs = self.prepare_filter_kwargs(kwargs)
        return super(QuerySet, self).filter(*args, **kwargs)

    @Manager.proxy_method
    def exclude(self, *args, **kwargs):
        if len(args) == 1 and hasattr(args[0], 'add_to_query'):
            q = ~args[0]                
            return self.complex_filter(q)
        kwargs = self.prepare_filter_kwargs(kwargs)
        return super(QuerySet, self).exclude(*args, **kwargs)

    @Manager.proxy_method
    def fetch(self, *args):
        return fetch(self, *args)
