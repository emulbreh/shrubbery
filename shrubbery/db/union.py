import bisect
import itertools
from django.db import connections
from django.db.models.query import QuerySet
from django.db.models.query_utils import deferred_class_factory
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE
from django.db.models.base import ModelBase, Model
from django.db.models.loading import cache as app_cache

from shrubbery.db.utils import get_query_set, get_sub_models
from shrubbery.utils import reduce_and
from shrubbery.utils.pycompat import *

MODEL_COL = '__model'

def sorted_union_generator(querysets, key=None, reverse=False):    
    sorted_seqs = []
    def _next(it):
        try:
            next = it.next()
            bisect.insort(sorted_seqs, (key(next), next, it))
        except StopIteration:
            pass
    for qs in querysets:
        _next(iter(qs))
    while sorted_seqs:
        if reverse:
            _, next, it = sorted_seqs.pop()
        else:
            _, next, it = sorted_seqs[0]
            del sorted_seqs[0]
        yield next
        _next(it)
        
def chained_union_generator(querysets, start=None, stop=None, step=None):
    offset = 0
    for qs in querysets:
        qs_start, qs_stop = None, None
        if start:
            qs_start = max(start - offset, 0)
        if stop:
            qs_stop = stop - offset
            if qs_stop <= 0 or (qs_start and qs_start >= qs_stop):
                break
        if qs_start or qs_stop:
            qs = qs[qs_start:qs_stop]
        for obj in qs:
            yield obj
        offset += len(qs)
        if qs_start:
            offset += qs_start

class UnionQuerySet(object):
    def __init__(self, *querysets):
        self.querysets = []
        self.querysets_by_model = {}
        for qs in querysets:
            self._add_qs(qs)
        self.limits = (None, None)
        self.sort_key = None
        self.sort_reverse = False
        
    def _add_qs(self, qs):
        if isinstance(qs, ModelBase) and qs._meta.abstract:
            for sub in get_sub_models(qs, direct=True):
                self._add_qs(sub)
        else:
            qs = get_query_set(qs)
            if qs.model in self.querysets_by_model:
                model_qs = self.querysets_by_model[qs.model]
                index = self.querysets.index(model_qs)
                qs = qs | model_qs
                self.querysets[index] = qs
            else:
                self.querysets.append(qs)
            self.querysets_by_model[qs.model] = qs
    
    def _clone(self, querysets=None):
        copy_querysets = querysets is None
        if copy_querysets:
            querysets = ()
        clone = type(self)(*querysets)
        if copy_querysets:
            clone.querysets = self.querysets[:]
            clone.querysets_by_model = self.querysets_by_model.copy()
        clone.limits = self.limits
        clone.sort_key = self.sort_key
        clone.sort_reverse = self.sort_reverse
        return clone
    
    def __iter__(self):
        if not self.sort_key:
            return chained_union_generator(self.querysets, *self.limits)
        else:
            start, stop = self.limits
            if stop:
                querysets = [qs[:stop] for qs in self.querysets]
            else:
                querysets = self.querysets
            sorted_it = sorted_union_generator(querysets, key=self.sort_key, reverse=self.sort_reverse)
            return itertools.islice(sorted_it, *self.limits)
            
    def sort(self, key=None, reverse=False):
        clone = self._clone()
        if key is None:
            key = lambda obj: obj
        elif isinstance(key, str):
            if key[0] == '-':
                reverse = not reverse
                attr = key[1:]
            else:
                attr = key
            def _sort_key(obj):
                return getattr(obj, attr)
            key = _sort_key
        clone.sort_key = key
        clone.sort_reverse = reverse
        return clone
        
    def __or__(self, other):
        if isinstance(other, (QuerySet, Model)):
            clone = self._clone()
            clone._add_qs(other)
            return clone
        elif isinstance(other, UnionQuerySet):
            clone = self._clone()
            for qs in other.querysets:
                clone._add_qs(qs)
            return clone
        raise TypeError
        
    def __and__(self, other):
        if isinstance(other, (QuerySet, Model)):
            other = get_query_set(other)
            qs = self.querysets_by_model.get(other.model, None)
            if not qs:
                return self._clone([])
            return self._clone([qs & other])
        elif isinstance(other, UnionQuerySet):
            models = self.models & other.models
            querysets = [self.querysets_by_model[model] & other.querysets_by_model[model] for model in models]
            return self._clone(querysets)
            
    def coerce(self, model):
        qs = self.querysets_by_model.get(model, None)
        if not qs:
            return get_query_set(model).none()
        return qs
            
    @property
    def models(self):
        return [qs.model for qs in self.querysets]
        
    @property
    def queries(self):
        return [qs.query for qs in self.querysets]
        
    def __getitem__(self, k):
        if isinstance(k, (int, long)):
            index = k
            for qs in self.querysets:
                try:
                    return qs[index]
                except IndexError:
                    index -= qs.count()
            raise IndexError
        elif isinstance(k, slice):
            clone = self._clone()
            clone.limits = (k.start, k.stop)
            return clone
        else:
            raise TypeError
        
    def __repr__(self):
        return repr(list(self))
        
    def order_and_sort_by(self, attr):
        return self.order_by(attr).sort(attr)
        
    def get_common_fields(self, check_type=True, local=True):
        model_fields = []
        for queryset in self.querysets:
            db = queryset.db
            fields_with_dbtype = set((field.name, field.db_type(connection=connections[db])) for field in queryset.model._meta.fields)
            model_fields.append(fields_with_dbtype)        
        return tuple(name for name, db_type in reduce_and(model_fields))

    def as_sql(self, fields=None):
        if not fields:
            fields = self.get_common_fields()
        sql_queries = []
        params = ()
        for index, qs in enumerate(self.querysets):
            values_qs = qs.extra(select={MODEL_COL: '%s'}, select_params=(index,)).values(MODEL_COL, *fields)            
            sql, qs_params = values_qs.query.get_compiler(values_qs.db).as_sql()
            sql_queries.append(sql)
            params += qs_params                    

        sql = 'SELECT * FROM (%s)' % ' UNION '.join(sql_queries)
        return sql, params
        
    def _execute_union(self, fields):
        # TODO: handle ordering, cache results
        # FIXME: this is horribly broken
        sql, params = self.as_sql(fields)
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = iter((lambda: cursor.fetchmany(GET_ITERATOR_CHUNK_SIZE)), connection.features.empty_fetchmany_value)
        for chunk in result:
            for row in chunk:
                yield row[0], dict(zip(fields, row[1:]))
        
    def fetch_values(self, fields=None):
        if not fields:
            fields = self.get_common_fields()        
        for model_index, values in self._execute_union(fields):
            yield values
                
    def fetch_objects(self, fields=None):
        if not fields:
            fields = self.get_common_fields()
        deferred_models = []
        for model in self.models:
            skip = set(field.attname for field in model._meta.fields if not field.name in fields)
            deferred_models.append(deferred_class_factory(model, skip))
        for model_index, values in self._execute_union(fields):
            yield deferred_models[model_index](**values)
        
    @classmethod
    def add_proxy(cls, name, return_map=None):
        def proxy(self, *args, **kwargs):
            try:
                funcs = [getattr(qs, name) for qs in self.querysets]
            except AttributeError:
                raise
            results = [func(*args, **kwargs) for func in funcs]
            return (return_map or self._clone)(results)
        proxy.__name__ = name
        setattr(cls, name, proxy)
        
_proxy_methods = (
    'distinct', 'all', 'order_by', 'select_related', 'reverse', 'complex_filter', 
    'exclude', 'filter', 'extra', 'dates', 'latest', 'none', 'values', 'values_list', 'annotate',
)

# Add QuerySet methods that return QuerySets.
for method in _proxy_methods:
    UnionQuerySet.add_proxy(method)
    
UnionQuerySet.add_proxy('__len__', sum)
UnionQuerySet.add_proxy('count', sum)
UnionQuerySet.add_proxy('__nonzero__', any)
    