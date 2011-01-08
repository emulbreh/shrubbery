from django.template import Library

def add_library(parser, library, namespaces=('')):
    for ns in namespaces:
        for t in library.tags:      
            parser.tags["%s%s" % (ns, t)] = library.tags[t]
        for f in library.filters:
            parser.filters["%s%s" % (ns, f)] = library.filters[f]


register = Library()


#{% import foo.bar %}
#{% import foo.bar as fbar %}
@register.tag(name='import')
def do_import(parser, token):
    bits = token.contents.split()
    if len(bits) > 1:
        path = bits[1]
        if len(bits) == 4 and bits[2] == 'as':
            alias = bits[3]
        elif len(bits) == 1:
            alias = path
        else:
            raise TemplateSyntaxError, "bad import tag syntax"
        try:
            lib = get_library(path)
            add_library(parser, lib, namespaces=('', alias))
        except InvalidTemplateLibrary, e:
            pass
        
        
        