from django.db import models

class VirtualField(models.Field):
    def class_prepared(self, cls):
        pass

    def contribute_to_class(self, cls, name):
        self.set_attributes_from_name(name)
        cls._meta.add_virtual_field(self)

def _setup_virtual_fields(sender=None, **kwargs):
    for field in sender._meta.virtual_fields:
        if isinstance(field, VirtualField):
            field.class_prepared(sender)

models.signals.class_prepared.connect(_setup_virtual_fields)

    