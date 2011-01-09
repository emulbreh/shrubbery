from itertools import izip
from django.db import models

from shrubbery.utils.text import camel_case
from shrubbery.db.utils import create_intermediate_model, clean_slice, get_model_ref, get_query_set
from shrubbery.db.fields import VirtualField
from shrubbery.db.transaction import commit_on_success_unless_managed

def create_manager_class(related, superclass):
    rel_field = related.field
    
    index_attr = rel_field.index
    value_attr = rel_field.value
    
    class ReverseListManager(superclass):
        ### normal manager methods ###

        def get_query_set(self):
            return super(ReverseListManager, self).get_query_set().order_by(index_attr)
        
        ### private utilities ###
        
        def _shift_gte(self, index, delta):
            if not delta:
                return
            self.filter(**{'%s__gte' % index_attr: index}).update(**{index_attr: models.F(index_attr) + delta})
            
        def _do_slice(self, s, target, lookup, filters=None):
            if not filters:
                filters = {}
            s = clean_slice(s, self.count, allow_step=(1, -1))
            if s.start and s.stop is not None:
                filters["%s__range" % lookup] = (s.start, s.stop - 1)
            elif s.start:
                filters["%s__gte" % lookup] = s.start
            elif s.stop is not None:
                filters["%s__lt" % lookup] = s.stop
            qs = target.filter(**filters)
            if s.step == -1:
                qs = qs.reverse()
            return qs            

        def _slice(self, s):
            return self._do_slice(s, self, index_attr)
            
        def _create_item(self, index, value):
            attrs = {index_attr: index, value_attr: value, rel_field.attname: self.core_filters.itervalues().next()}
            item = self.model(**attrs)
            item.save(force_insert=True)
            return item
            
        def _update_item(self, index, value):
            return self.filter(**{index_attr: index}).update(**{value_attr: value})
            
        def _get_item(self, index):
            return self.get(**{index_attr: index})
            
        def _get_items_for_value(self, value):
            return self.filter(**{value_attr: value})
            
        def _get_item_for_value(self, value):
            return self._get_items_for_value(value)[:1].get()
            
        ### list methods that clash with manager methods ###
        
        def count(self, *args):
            if len(args) == 1:
                return self._get_items_for_value(args[0]).count()
            return super(ReverseListManager, self).count(*args)

        def reverse(self):
            values = list(iter(self))
            values.reverse()
            for index, item in enumerate(values):
                self._update_item(index, value)
                
        @commit_on_success_unless_managed
        def remove(self, value):
            try:
                item = self._get_item_for_value(value)
            except self.model.DoesNotExist:
                raise ValueError("%r not in list" % value)
            item.delete()
            self._shift_gte(getattr(item, index_attr), -1)
                
        ### list methods ###

        def __nonzero__(self):
            return self.exists()

        def __len__(self):
            return super(ReverseListManager, self).count()

        def __contains__(self, value):
            return self._get_items_for_value(value).exists()

        def __iter__(self):
            for item in self.all():
                yield getattr(item, value_attr)

        def __getitem__(self, index):
            if isinstance(index, slice):
                return rel_field.slice(self, index)
            try:
                return getattr(self._get_item(index), value_attr)
            except self.model.DoesNotExist:
                raise IndexError("index out of range")
        
        @commit_on_success_unless_managed
        def __setitem__(self, index, value):
            if isinstance(index, slice):
                s = clean_slice(index, self.count, replace_none=True, allow_step=(1,))
                indices = iter(xrange(s.start, s.stop, s.step))
                values = iter(value)
                enum = izip(indices, values)
                extended = False
                for i, val in enum:
                    found = self._update_item(i, val)
                    if not found:
                        extended = True
                        self._create_item(i, val)
                        for i, val in enum:
                            self._create_item(i, val)
                try:
                    # are there more indices than values?
                    i = indices.next()
                    if not extended:
                        del self[i:s.stop]
                except StopIteration:
                    # no more indices, then there might be more values
                    val_list = list(values)
                    if val_list and not extended:
                        self._shift_gte(s.stop, len(val_list))
                    for i, val in enumerate(val_list):
                        self._create_item(s.stop + i, val)
            else:           
                found = self._update_item(index, value)
                if not found:
                    raise IndexError("assignment index out of range")

        @commit_on_success_unless_managed
        def __delitem__(self, index):
            if isinstance(index, slice):
                s = clean_slice(index, self.count, allow_step=(1,))
                items = self._slice(s)
                count = items.count()
                items.delete()
                if s.stop is not None:
                    self._shift_gte(s.stop, -count)
            else:
                try:
                    self.pop(index)
                except self.model.DoesNotExist:
                    raise IndexError("assignment index out of range")

        @commit_on_success_unless_managed
        def insert(self, index, value):
            self[index:index] = [value]

        @commit_on_success_unless_managed
        def append(self, value):
            self._create_item(self.count(), value)

        @commit_on_success_unless_managed
        def extend(self, seq):
            count = self.count()
            for index, value in enumerate(seq):
                self._create_item(count + index, value)

        @commit_on_success_unless_managed
        def pop(self, index=None):
            if index is None:
                index = self.count() - 1
            elif index < 0:
                index = self.count() + index
            if index < 0:
                raise IndexError("index out of range")
            try:
                item = self._get_item(index)
            except self.model.DoesNotExist:
                raise IndexError("index out of range")
            value = getattr(item, value_attr)
            item.delete()
            self._shift_gte(index, -1)
            return value

        @commit_on_success_unless_managed
        def sort(self, *args, **kwargs):
            values = list(iter(self))
            values.sort(*args, **kwargs)
            for index, value in enumerate(values):
                self._update_item(index, value)
                
        @commit_on_success_unless_managed
        def index(self, value, lower=None, upper=None):
            try:
                item = self._get_item_for_value(value)
                return getattr(item, index_attr)
            except self.model.DoesNotExist:
                raise ValueError("%r not in list" % value)

    return ReverseListManager

def _unsupported_manager_method(*args, **kwargs):
    raise TypeError("unsupported manager method")

class ReverseListDescriptor(models.fields.related.ForeignRelatedObjectsDescriptor):
    def create_manager(self, instance, superclass):
        manager_cls = create_manager_class(self.related, superclass)
        manager = super(ReverseListDescriptor, self).create_manager(instance, manager_cls)
        manager.create = _unsupported_manager_method
        return manager

    def __set__(self, instance, values):
        manager = self.__get__(instance)
        manager.all().delete()
        for index, value in enumerate(iter(values)):
            manager._create_item(index, value)


class ReverseListField(models.ForeignKey):
    def __init__(self, to, index='index', value='value', **kwargs):
        assert kwargs.get('null', False) is False, "ReverseDictField may not be null"
        super(ReverseListField, self).__init__(to, **kwargs)
        self.index = index
        self.value = value

    def slice(self, manager, s):
        return [getattr(item, self.value) for item in manager._slice(s)]

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), ReverseListDescriptor(related))

def create_list_model(cls, name, value_field, index='index', value='value', db_table=None, field_cls=ReverseListField):
    class_ptr_name = cls.__name__.lower()
    attrs = {
        class_ptr_name: field_cls(get_model_ref(cls), related_name=name, index=index, value=value),
        index: models.PositiveIntegerField(),
        value: value_field,
    }
    meta = {
        'unique_together': (class_ptr_name, index),
    }
    if db_table:
        meta['db_table'] = db_table
    return create_intermediate_model(cls, name, attrs, meta=meta)        

class ListField(VirtualField):
    def __init__(self, value_field, **kwargs):
        if isinstance(value_field, (str, models.base.ModelBase)):
            value_field = models.ForeignKey(value_field, 
                null=kwargs.pop('null', False), 
                blank=kwargs.pop('blank', False), 
                related_name=kwargs.pop('related_name', None),
            )
        else:
            assert "null" not in kwargs, "ListField does not support `null`, use `null` on its value field."
            assert "blank" not in kwargs, "ListField does not support `blank`, use `blank` on its value field."            
        self.value_field = value_field
        self.index_field_name = kwargs.pop('index_field_name', 'index')
        self.value_field_name = kwargs.pop('value_field_name', 'value')
        self.db_table = kwargs.pop('db_table', None)
        super(VirtualField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        super(ListField, self).contribute_to_class(cls, name)
        self.list_model = create_list_model(cls, name, self.value_field, 
            index=self.index_field_name, 
            value=self.value_field_name, 
            db_table=self.db_table,
            field_cls=ReverseListField,
        )

### ManyToManyList support ###

class ReverseManyToManyListField(ReverseListField):
    def slice(self, manager, s):
        value_field = manager.model._meta.get_field(self.value)
        rel_name = value_field.rel.related_name
        filters = {}
        for lookup, value in manager.core_filters.items():
            filters['%s__%s' % (rel_name, lookup)] = value
        target = get_query_set(value_field.rel.to)        
        return manager._do_slice(s, target, rel_name, filters)

class ManyToManyList(models.ManyToManyField):
    def __init__(self, to, **kwargs):
        assert "through" not in kwargs, "ManyToManyList cannot use an explicit through model."
        self.list_descriptor = kwargs.pop('list_descriptor', None)
        self.index_field_name = kwargs.pop('index_field_name', 'index')
        self.value_field_name = kwargs.pop('value_field_name', 'value')        
        super(ManyToManyList, self).__init__(to, **kwargs)
        
    def contribute_to_class(self, cls, name):
        if not self.list_descriptor:
            self.list_descriptor = "%s_list" % name.replace('_set', '')
        to = self.rel.to
        self.rel.through = create_list_model(cls, self.list_descriptor, models.ForeignKey(to), 
            index=self.index_field_name, 
            value=self.value_field_name, 
            db_table=self.db_table,
            field_cls=ReverseManyToManyListField,
        )
        self.creates_table = False
        super(ManyToManyList, self).contribute_to_class(cls, name)
        
        
        
