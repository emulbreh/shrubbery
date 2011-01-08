from django import forms
from shrubbery.tagging.encoding import parse_tags, encode_tags
from shrubbery.tagging.models import get_tags

class TagWidget(forms.TextInput):
    def render(self, name, value, attrs=None, choices=()):
        value_list = encode_tags(value or ())
        return super(TagWidget, self).render(name, value_list, attrs=attrs)


class TagField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', TagWidget())
        kwargs.setdefault('required', False)
        super(TagField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(TagField, self).clean(value)
        tag_names = list(parse_tags(value))
        return get_tags(tag_names, create=True)
        
    def prepare_value(self, value):
        return get_tags(value or ())
        

        