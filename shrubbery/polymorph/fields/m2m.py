from django.db import models, connection
from django.db.models.query import QuerySet

from shrubbery.utils.text import camel_case
from shrubbery.db.utils import no_related_name, create_intermediate_model
from shrubbery.db import extensions as ext
from shrubbery.polymorph.models import ObjectIdentity, ObjectIdentityManager

def create_intermediary_model(m2m, model, name):
    is_polymorph = m2m.to_field is None
    
    if is_polymorph:
        source, target = m2m.rel.to, model
    else:
        source, target = model, m2m.rel.to
        
    if source._meta.abstract:
        return None

    if not is_polymorph:
        table = m2m.to_field.rel.through._meta.db_table
    elif m2m.explicit_db_table:
        table = m2m.explicit_db_table
    else:
        table = "%s_%s_%s_rel" % (model._meta.app_label, model.__name__.lower(), name)
    
    on_delete = models.CASCADE if is_polymorph else models.DO_NOTHING,
    
    attrs = dict(
        obj = models.ForeignKey(source, related_name=no_related_name(), on_delete=on_delete),
        rel_obj = models.ForeignKey(target, related_name=no_related_name(), on_delete=on_delete),
        Meta = type('Meta', (object,), dict(
            managed=is_polymorph, 
            db_table=table,
            auto_created=model,
            unique_together=('obj', 'rel_obj'),
        )),
        __module__ = target.__module__,
    )
    
    through = type('%s%s' % (model.__name__, camel_case(name, True)), (models.Model,), attrs)
    return through


class ReverseManyToManyField(ext.ManyToManyField):
    def __init__(self, to, to_field, **kwargs):
        assert "through" not in kwargs, "Polymorph ReverseField cannot use `through`."
        assert "db_table" not in kwargs, "Polymorph ReverseField cannot use `db_table`, use the corresponding polymorph.ManyToManyField's argument instead."
        assert not kwargs.pop("symmetrical", False), "Polymorph ReverseField cannot be symmetrical."
        self.to_field = to_field
        kwargs.setdefault('related_name', None)
        super(ReverseManyToManyField, self).__init__(to, **kwargs)

    def contribute_to_class(self, cls, name):
        self.rel.through = create_intermediary_model(self, cls, name)
        super(ReverseManyToManyField, self).contribute_to_class(cls, name)                    


class ManyToManyField(ReverseManyToManyField):
    def __init__(self, **kwargs):
        self.explicit_db_table = kwargs.pop('db_table', None)
        kwargs.pop('to', None)
        super(ManyToManyField, self).__init__(ObjectIdentity, None, **kwargs) 
        
try:
    from south.modelsinspector import add_ignored_fields, add_introspection_rules
    add_ignored_fields(['^shrubbery\.polymorph\.fields\.m2m\.ReverseManyToManyField$'])
    add_introspection_rules([], ['^shrubbery\.polymorph\.fields\.m2m\.ManyToManyField$'])
except ImportError:
    pass

    