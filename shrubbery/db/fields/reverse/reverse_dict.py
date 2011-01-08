from django.db import models
from django.db.transaction import commit_on_success

from shrubbery.db.utils import create_intermediate_model, get_q
from shrubbery.db.fields import VirtualField
from shrubbery.db.transaction import commit_on_success_unless_managed

def create_manager_class(related, superclass):
    rel_field = related.field
    
    key_attr = rel_field.key
    value_attr = rel_field.value
    
    class ReverseDictManager(superclass):
        ### private utilities ###

        def _create_item(self, key, value):
            return self.create(**{key_attr: key, value_attr: value})
            
        def _update_item(self, key, value):
            return self.filter(**{key_attr: key}).update(**{value_attr: value})

        def _get_item(self, key):
            return self.get(**{key_attr: key})        
        
        ### dict methods that clash with manager methods ###
        
        def get(self, *args, **kwargs):
            if len(args) in (1,2) and not kwargs:
                try:
                    get_q(args[0])
                except ValueError:
                    try:
                        return self[args[0]]
                    except KeyError:
                        if len(args) == 2:
                            return args[1]
                        return None
            return super(ReverseDictManager, self).get(*args, **kwargs)
            
        @commit_on_success_unless_managed
        def update(self, *args, **kwargs):
            if len(args) == 1 and not kwargs:
                for key, value in args[0].iteritems():
                    self[key] = value
            return super(ReverseDictManager, self).update(*args, **kwargs)

        ### dict methods ###
        
        def __len__(self):
            return self.count()
            
        def __nonzero__(self):
            return self.exists()

        def __contains__(self, key):
            try:
                self._getitem(key)
                return True
            except self.model.DoesNotExist:
                return False

        def __getitem__(self, key):
            try:
                return getattr(self._get_item(key), value_attr)
            except self.model.DoesNotExist:
                raise KeyError

        @commit_on_success_unless_managed
        def __delitem__(self, key):
            try:
                self._get_item(key).delete()
            except self.model.DoesNotExist:
                raise KeyError()

        @commit_on_success_unless_managed                
        def __setitem__(self, key, value):
            found = self._update_item(key, value)
            if not found:
                self._create_item(key, value)

        @commit_on_success_unless_managed
        def clear(self):
            self.all().delete()

        def iteritems(self):
            for item in self.all():
                yield (getattr(item, key_attr), getattr(item, value_attr))

        def items(self):
            return list(self.iteritems())

        def iterkeys(self):
            for item in self.all():
                yield getattr(item, key_attr)

        def itervalues(self):
            for item in self.all():
                yield getattr(item, value_attr)

        def __iter__(self):
            return self.iterkeys()
            
        def keys(self):
            return list(self.iterkeys())
            
        def values(self):
            return list(self.itervalues())
            
        @commit_on_success_unless_managed
        def setdefault(self, key, default=None):
            try:
                return self[key]
            except KeyError:
                self._create_item(key, default)
                return default

        @commit_on_success_unless_managed
        def pop(self, key, *args):
            try:
                item = self._get_item(key)
                value = getattr(item, value_attr)
                item.delete()
                return value
            except self.model.DoesNotExist:
                if args:
                    if len(args) == 1:
                        return args[0]
                    raise TypeError("pop expected at most 2 arguments, got %s" % (len(args) + 1))
                raise KeyError()
                
        @commit_on_success_unless_managed
        def popitem(self):
            try:
                item = self.all()[0]
                key, value = getattr(item, key_attr), getattr(item, value_attr)
                item.delete()
                return key, value
            except self.model.DoesNotExist:
                raise KeyError()
                
        def copy(self):
            return dict(self.iteritems())
                
    return ReverseDictManager


class ReverseDictDescriptor(models.fields.related.ForeignRelatedObjectsDescriptor):
    def create_manager(self, instance, superclass):
        manager_cls = create_manager_class(self.related, superclass)
        return super(ReverseDictDescriptor, self).create_manager(instance, manager_cls)         

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        for key in value:
            manager[key] = value[key]

class ReverseDictField(models.ForeignKey):
    def __init__(self, target, key='key', value='value', **kwargs):
        assert kwargs.get('null', False) is False, "ReverseDictField may not be null"
        super(ReverseDictField, self).__init__(target, **kwargs)
        self.value = value
        self.key = key      
        
    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), ReverseDictDescriptor(related))
        
class DictField(VirtualField):
    def __init__(self, key_field=None, value_field=None, key_field_name='key', value_field_name='value', **kwargs):
        self.key_field = key_field
        self.value_field = value_field
        self.key_field_name = key_field_name
        self.value_field_name = value_field_name
        super(DictField, self).__init__(**kwargs)
        
    def class_prepared(self, cls):
        class_ptr_name = cls.__name__.lower()
        attrs = {
            class_ptr_name: ReverseDictField(related_name=self.name, key=self.key_field_name, value=self.value_field_name),
            self.key_field_name: self.key_field,
            self.value_field_name: self.value_field,
        }
        self.dict_model = create_intermediate_model(cls, self.name, attrs, meta={
            'unique_together': (class_ptr_name, self.value_field_name),
        })
        