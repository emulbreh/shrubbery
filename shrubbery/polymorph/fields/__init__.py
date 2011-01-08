from shrubbery.polymorph.fields.m2m import ManyToManyField, ReverseManyToManyField
from shrubbery.polymorph.fields.fk import ForeignKey, ReverseForeignKey, OneToOneField, ReverseOneToOneField
from shrubbery.db.utils import get_by_ref

class ReverseField(object):
    def __init__(self, to, to_field, **kwargs):
        self.to = to
        self.to_field = to_field
        self.kwargs = kwargs

    def create_reverse_field(self, cls, name, to):
        to_field = to._meta.get_field(self.to_field)
        if isinstance(to_field, OneToOneField):
            field_cls = ReverseOneToOneField
        elif isinstance(to_field, ForeignKey):
            field_cls = ReverseForeignKey
        elif isinstance(to_field, ManyToManyField):
            field_cls = ReverseManyToManyField
        else:
            raise ValueError("polymorph.ReverseField must relate to a polymorph.ManyToManyField or polymorph.ForeignKey")        
        field_cls(to, to_field, **self.kwargs).contribute_to_class(cls, name)

    def contribute_to_class(self, cls, name):
        if isinstance(self.to, basestring):
            get_by_ref(self.to, lambda to: self.create_reverse_field(cls, name, to), app_label=cls._meta.app_label)
        else:
            self.create_reverse_field(cls, name, self.to)
            

