from django.db import models
from shrubbery.db import extensions as ext
from shrubbery.db.utils import get_sub_models, no_related_name

from shrubbery.polymorph.models import Object, ObjectIdentity

class ForeignKeyDescriptor(models.fields.related.ReverseSingleRelatedObjectDescriptor):
    def __set__(self, instance, value):
        if isinstance(value, Object):
            assert value.pk, "Cannot assign unsaved Object instances."
            value = value.id
        super(ForeignKeyDescriptor, self).__set__(instance, value)

class PolymorphFieldMixin(object):
    def __init__(self, **kwargs):
        kwargs.setdefault('related_name', None)
        super(PolymorphFieldMixin, self).__init__(ObjectIdentity, **kwargs)
    
    def get_prep_lookup(self, lookup_type, obj):
        if isinstance(obj, Object):
            assert obj.pk, "Cannot use unsaved Object instances as lookup values."
            obj = obj.id
        return super(PolymorphFieldMixin, self).get_prep_lookup(lookup_type, obj)

    def contribute_to_class(self, cls, name):
        super(PolymorphFieldMixin, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ForeignKeyDescriptor(self))

class ForeignKey(PolymorphFieldMixin, ext.ForeignKey): pass
class OneToOneField(PolymorphFieldMixin, ext.OneToOneField): pass

class ShadowFieldMixin(object):
    def __init__(self, *args, **kwargs):
        super(ShadowFieldMixin, self).__init__(*args, **kwargs)
        self.db_index = False

    def db_type(self, connection):
        return None

    def contribute_to_class(self, cls, name):
        models.Field.contribute_to_class(self, cls, name)
        #self.related_query_name = curry(self._get_related_query_name, cls._meta)

class ForeignKeyShadow(ShadowFieldMixin, ext.ForeignKey): pass
class OneToOneFieldShadow(ShadowFieldMixin, ext.OneToOneField): pass
        
class ReverseForeignKey(object):
    descriptor_cls = models.fields.related.ForeignRelatedObjectsDescriptor
    reverse_name_pattern = "_polymorph_o2m_reverse_%s"
    shadow_field_class = ForeignKeyShadow

    def __init__(self, to, to_field):
        self.to = to
        self.to_field = to_field

    def contribute_to_class(self, cls, name):
        rel_obj = models.related.RelatedObject(cls, self.to, self.to_field)
        setattr(cls, name, self.descriptor_cls(rel_obj))
        
        reverse_name = self.reverse_name_pattern % cls.__name__.lower()
        fk = self.shadow_field_class(cls, related_name=name, to_field='id', db_column=self.to_field.column)
        fk.contribute_to_class(self.to, reverse_name)
            

class ReverseOneToOneField(ReverseForeignKey):
    descriptor_cls = models.fields.related.SingleRelatedObjectDescriptor
    reverse_name_pattern = "_polymorph_o2o_reverse_%s"
    shadow_field_class = OneToOneFieldShadow


try:
    from south.modelsinspector import add_ignored_fields, add_introspection_rules
    add_ignored_fields(['^shrubbery\.polymorph\.fields\.fk\..+Shadow$'])
    add_introspection_rules([], ['^shrubbery\.polymorph\.fields\.fk\.ForeignKey$', '^shrubbery\.polymorph\.fields\.fk\.OneToOneField$'])
except ImportError:
    pass
