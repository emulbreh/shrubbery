from django.db import models as django_models

from shrubbery.db.utils import no_related_name

def _get_prep_lookup(lookup, value):
    if lookup == 'in' and isinstance(value, django_models.query.QuerySet):
        value = value.values('pk').query
    return value

class ForeignRelatedObjectsDescriptor(django_models.fields.related.ForeignRelatedObjectsDescriptor):
    def create_manager(self, instance, superclass):
        field = self.related.field
        superclass = field.related_manager_class or superclass
        cls = super(ForeignRelatedObjectsDescriptor, self).create_manager(instance, superclass)
        if field.related_manager_class_decorator:
            cls = field.related_manager_class_decorator(cls)
        return cls


class ForeignKey(django_models.ForeignKey):
    def __init__(self, *args, **kwargs):        
        self.related_manager_class = kwargs.pop('related_manager_class', None)
        self.related_manager_class_decorator = kwargs.pop('related_manager_class_decorator', None)
        
        if 'related_name' in kwargs and not kwargs['related_name']:
            kwargs['related_name'] = no_related_name()        
        
        super(ForeignKey, self).__init__(*args, **kwargs)
        
    def contribute_to_related_class(self, cls, related):
        super(ForeignKey, self).contribute_to_related_class(cls, related)
        if self.related_manager_class or self.related_manager_class_decorator:
            setattr(cls, related.get_accessor_name(), ForeignRelatedObjectsDescriptor(related))

    def get_prep_lookup(self, lookup, value):
        value = _get_prep_lookup(lookup, value)
        return super(ForeignKey, self).get_prep_lookup(lookup, value)


class OneToOneField(django_models.OneToOneField):
    def __init__(self, *args, **kwargs):
        if 'related_name' in kwargs and not kwargs['related_name']:
            kwargs['related_name'] = no_related_name()        
        super(OneToOneField, self).__init__(*args, **kwargs)
        
    def get_prep_lookup(self, lookup, value):
        value = _get_prep_lookup(lookup, value)
        return super(OneToOneField, self).get_prep_lookup(lookup, value)


class ManyToManyDescriptor(object):
    def __init__(self, field, target_model, source_field_name, target_field_name, query_name, superclass=None, class_decorator=None):
        self.field = field
        self.target_model = target_model
        self.source_field_name = source_field_name
        self.target_field_name = target_field_name
        self.query_name = query_name
        self.superclass = superclass
        self.class_decorator = class_decorator
        
    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        model = self.target_model()
        superclass = self.superclass or self.target_model._default_manager.__class__
        cls = django_models.fields.related.create_many_related_manager(superclass, self.field.rel)
        if self.class_decorator:
            cls = class_decorator(cls)
        return cls(
            model=model,
            core_filters={'%s__pk' % self.query_name(): instance.pk},
            instance=instance,
            symmetrical=False,
            source_field_name=self.source_field_name(),
            target_field_name=self.target_field_name()
        )
        
    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError, "Manager must be accessed via instance"

        manager = self.__get__(instance)
        if hasattr(manager, 'assign'):
            manager.assign(value)
        else:
            manager.clear()
            manager.add(*value)
        

class ManyToManyField(django_models.ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.manager_class = kwargs.pop('manager_class', None)
        self.manager_class_decorator = kwargs.pop('manager_class_decorator', None)
        self.related_manager_class = kwargs.pop('related_manager_class', None)
        self.related_manager_class_decorator = kwargs.pop('related_manager_class_decorator', None)
        
        if 'related_name' in kwargs and not kwargs['related_name']:
            kwargs['related_name'] = no_related_name()
            
        super(ManyToManyField, self).__init__(*args, **kwargs)
        
    def contribute_to_class(self, cls, name):
        super(ManyToManyField, self).contribute_to_class(cls, name)
        if self.manager_class or self.manager_class_decorator:
            descr = ManyToManyDescriptor(self, 
                lambda: self.rel.to, 
                lambda: self.m2m_field_name(), 
                lambda: self.m2m_reverse_field_name(), self.related_query_name,
                self.manager_class, self.manager_class_decorator)
            setattr(cls, self.name, descr)
        
    def contribute_to_related_class(self, cls, related):
        super(ManyToManyField, self).contribute_to_related_class(cls, related)
        if self.related_manager_class or self.related_manager_class_decorator:
            descr = ManyToManyDescriptor(self, lambda: related.model, self.m2m_reverse_field_name, self.m2m_field_name, lambda: self.name, 
                self.related_manager_class, self.related_manager_class_decorator)
            setattr(cls, related.get_accessor_name(), descr)
    
    def get_prep_lookup(self, lookup, value):
        value = _get_prep_lookup(lookup, value)
        return super(ManyToManyField, self).get_prep_lookup(lookup, value)

    try:
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], [r'^shrubbery\.db\.extensions\.rel_fields\.(ForeignKey|OneToOneField|ManyToManyField)$'])
    except ImportError:
        pass
