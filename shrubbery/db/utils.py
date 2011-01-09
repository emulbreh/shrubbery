import re
from django.db import models

from shrubbery.utils.text import camel_case

def no_related_name(hidden=False):
    no_related_name._next += 1
    name = "_no_related_name_%%(class)s_%s" % (no_related_name._next)
    if hidden:
        name += '+'
    return name
no_related_name._next = 0

def _remove_related_accessors(sender, **kwargs):
    for attr in dir(sender):
        if attr.startswith('_no_related_name_'):
            # delete() requires related descriptors - stupid multi-manager code
            #delattr(sender, attr)
            pass
models.signals.class_prepared.connect(_remove_related_accessors)


class ImplicitQMixin(object):
    def as_q(self):
        return models.Q()

    def add_to_query(self, query, aliases=None):
        query.add_q(self.as_q())

    def __and__(self, other):
        return self.as_q() & other

    def __or__(self, other):
        return self.as_q() | other

    def __invert__(self):
        return ~self.as_q()
        

class CompoundQ(object):
    def __init__(self, objects, conjunction=True):
        self.objects = objects
        self.conjunction = conjunction
        
    def __invert__(self):
        return self.__class__([~obj for obj in self.objects], not self.conjunction)
        
    def combine(self, other, conjunction):
        if self.conjunction == conjunction:
            # If the connection type is equal, we can avoid further nesting
            objects = None
            if isinstance(other, models.Q):
                # If we already have a builtin Q, we can just add `other` one to it.
                for index, obj in enumerate(self.objects):
                    if isinstance(obj, models.Q):
                        objects = self.objects[:]
                        if self.conjunction:                    
                            objects[index] &= other
                        else:
                            objects[index] |= other
                        break
            elif isinstance(other, CompoundQ) and other.conjunction == conjunction:
                # Two CompoundQ objects may be combined in a single new object without nesting
                objects = self.objects + other.objects
            if not objects:
                objects = self.objects + [other]
            return self.__class__(objects, conjunction)
        return CompoundQ([self, other], conjunction)

    def __and__(self, other):
        return self.combine(other, True)
        
    def __or__(self, other):
        return self.combine(other, False)
        
    def __rand__(self, other):
        # Since '&' is supposed to be commutative
        return self & other
        
    def __ror__(self, other):
        # Since '|' is supposed to be commutative
        return self | other

    @property
    def connector(self):
        return self.conjunction and models.sql.where.AND or models.sql.where.OR
    
    def add_to_query(self, query, aliases):
        clones = [query.clone().add_q(obj) for obj in self.objects[1:]]
        query.add_q(self.objects[0])
        for clone in clones:
            query.combine(clone, self.connector)


def get_q(obj):
    if isinstance(obj, dict):
        return models.Q(**obj)
    if hasattr(obj, 'add_to_query') or isinstance(obj, models.Q):
        return obj
    if hasattr(obj, 'as_q'):
        return obj.as_q()
    raise ValueError()


def get_model(obj, allow_import=False, proxy=True):
    if isinstance(obj, models.base.ModelBase):
        model = obj
    elif isinstance(obj, models.Model):
        model = obj.__class__
    elif hasattr(obj, 'model'):
        return obj.model
    elif allow_import and isinstance(obj, str):
        module_name, name = obj.rsplit('.')
        module = import_module(module_name)
        model = getattr(module, name)
    else:
        raise ValueError
    if not proxy:
        while model._meta.proxy:
            model = model._meta.proxy_for_model
    return model
    

def get_manager(obj):
    if isinstance(obj, models.Manager):
        return obj
    if isinstance(obj, models.base.ModelBase):
        return obj._default_manager
    raise ValueError


def get_query_set(obj):
    """ Returns a QuerySet for a given QuerySet, Manager, Model, or an object with a get_query_set() method. """
    if isinstance(obj, models.query.QuerySet):
        return obj
    if isinstance(obj, models.Manager):
        return obj.all()
    if isinstance(obj, models.base.ModelBase):
        return obj._default_manager.all()
    if hasattr(obj, 'get_query_set'):
        return obj.get_query_set()
    raise ValueError
    

def fetch(qs, *args):
    qs = get_query_set(qs)
    for arg in args:
        try:
            q = get_q(arg)
        except ValueError:
            if callable(arg):
                try:
                    arg = arg()
                except qs.model.DoesNotExist:
                    continue
            if isinstance(arg, Exception):
                raise arg
            return arg
        try:
            return qs.get(q)
        except qs.model.DoesNotExist:
            pass
    raise qs.model.DoesNotExist()
    

def _collect_sub_models(model, abstract, proxy, virtual, direct, sub_models):
    for subclass in model.__subclasses__():
        if (abstract or not subclass._meta.abstract) and (proxy or not subclass._meta.proxy) and (virtual or not getattr(subclass._meta, 'virtual', False)):
            sub_models.add(subclass)
            if direct:
                continue
        _collect_sub_models(subclass, abstract, proxy, virtual, direct, sub_models)
    return sub_models


_sub_models_cache = {}


def get_sub_models(model, abstract=False, proxy=False, virtual=False, direct=False):
    cache_key = (model, abstract, proxy, direct)
    if cache_key not in _sub_models_cache:
        _sub_models_cache[cache_key] = _collect_sub_models(model, abstract, proxy, virtual, direct, set())
    return _sub_models_cache[cache_key]


# django.db.models.sql.Query utilities

def force_empty(query):
    query.add_extra(None, None, ("1=0",), None, None, None)


def remove_join(query, alias, traceless=False):
    """Removes the join from query.join_map, query.alias_map, and query.rev_join_map. 
    If `traceless=True`, removes it from query.tables and query.alias_refcount as well."""
    t_ident = query.rev_join_map[alias]
    jm_list = list(query.join_map[t_ident])
    jm_list.remove(alias)
    query.join_map[t_ident] = tuple(jm_list)
    del query.rev_join_map[alias]
    del query.alias_map[alias]
    if traceless:
        query.tables.remove(alias)
        del query.alias_refcount[alias]        


def forge_join(query, table, alias, lhs, lhs_alias, lhs_col, col, nullable=False, join_type=None):
    """Updates query.join_map, query.alias_map, and query.rev_join_map. 
    This can be used to replace an existing join or to create a new join."""
    if not join_type:
        join_type = query.INNER
    query.alias_map[alias] = (table, alias, join_type, lhs_alias, lhs_col, col, nullable)
    t_ident = (lhs, table, lhs_col, col)
    if t_ident in query.join_map:
        query.join_map[t_ident] += (alias,)
    else:
        query.join_map[t_ident] = (alias,)        
    query.rev_join_map[alias] = t_ident        


# Misc

def replace_text(pattern, replacement, model):
    if isinstance(pattern, (unicode, str)):
        pattern = re.compile(pattern)
    fields = []
    for field in model._meta.fields:
        if isinstance(field, (models.TextField, models.CharField)):
            fields.append(field.name)
    for obj in get_query_set(model):
        for field in fields:
            val = getattr(obj, field)
            if val and pattern.search(val):
                val = pattern.sub(replacement, val)
                setattr(obj, field, val)
                obj.save()


def unordered_pairs(qs):
    objects = list(qs.order_by())
    for a in objects:
        for b in objects:
            if b.pk > a.pk:
                yield a, b


def create_intermediate_model(cls, rel_name, attrs, bases=None, meta=None):
    if not meta:
        meta = {}
    if not bases:
        bases = (models.Model,)
    meta.setdefault('app_label', cls._meta.app_label)    
    attrs['Meta'] = type('Meta', (object,), meta)
    attrs.setdefault('__module__', cls.__module__)
    return type("%s%s" % (cls.__name__, camel_case(rel_name, True)), bases, attrs)
    

def clean_slice(s, count_func, replace_none=False, allow_step=True):
    start, stop, step = s.start, s.stop, s.step
    if callable(count_func):
        count = None
    else:
        count = count_func
    if start is None:
        if replace_none:
            start = 0
    elif start < 0:
        if count is None:
            count = count_func()
        start = max(count + start, 0)
    if stop is None:
        if replace_none:
            if count is None:
                count = count_func()
            stop = count
    elif stop < 0:
        if count is None:
            count = count_func()
        stop = max(count + stop, 0)
    if step is None and replace_none:
        step = 1
    if step and allow_step is not True and step not in allow_step:
        raise ValueError("unsupported slice.step")
    return slice(start, stop, step)


def get_model_ref(model):
    if isinstance(model, str):
        return model
    return "%s.%s" % (model._meta.app_label, model.__name__)


def get_app_path(module):
    for app in settings.INSTALLED_APPS:
        if app.startswith(module):
            if app == module or module[len(app)] == '.':
                return app
    raise ValueError
    

def get_app_label(module):
    return get_app_path(module).rsplit('.', 1)[-1]


_pending_reference_lookups = {}

def get_by_ref(s, callback, module=None, app_label=None, field=None):
    if '@' in s:
        model, module_name = s.split('@')
        if module_name:
            app_label = None
            module = module_name
        if '.' in name:
            model, field = name.split('.')
    else:
        bits = s.rsplit('.', 3)
        if len(bits) == 1:
            model = bits[0]
        elif len(bits) == 2:
            app_label, model = bits
        else:
            app_label, model, field = bits
    
    if module and not app_label:
        app_label = get_app_label(module)        
    
    if app_label:
        from django.db.models.loading import get_model
        model = get_model(app_label, model)
    else:
        from django.db.models.loading import get_models
        for m in get_model():
            if m.__name__ == model:
                model = m
                break
    if not model:
        _pending_reference_lookups.setdefault((app_label, model), []).append((field, callback))
    else:
        _fire_ref_callback(model, field, callback)
            
def _fire_ref_callback(model, field, callback):
    if field:
        callback(model._meta.get_field(field))
    else:
        callback(model)    

def _do_pending_reference_lookups(sender, **kwargs):
    field, callback = _pending_reference_lookups.pop((sender._meta.app_label, sender.__name__), (None, None))
    if callback:
        _fire_ref_callback(sender, field, callback)

models.signals.class_prepared.connect(_do_pending_reference_lookups)