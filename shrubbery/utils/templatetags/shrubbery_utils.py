import re
from django import template
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils import simplejson

register = template.Library()

def mapped_filter(func):
    def f(value, arg=None):
        if arg:
            try:
                value = [getattr(val, arg) for val in value]
            except AttributeError:
                return None
        return func(value)
    return f

register.filter(name='concat')(lambda a, b: "%s%s" % (a, b))
register.filter(name='contains')(lambda a, b: b in a)
register.filter(name='in')(lambda a, b: a in b)
register.filter(name='eq')(lambda a, b: a == b)
register.filter(name='lt')(lambda a, b: a < b)
register.filter(name='le')(lambda a, b: a <= b)
register.filter(name='gt')(lambda a, b: a > b)
register.filter(name='ge')(lambda a, b: a >= b)
register.filter(name='add')(lambda a, b: a + b)
register.filter(name='sub')(lambda a, b: a - b)
register.filter(name='mul')(lambda a, b: a * b)
register.filter(name='neg')(lambda a: -a)
register.filter(name='invert')(lambda a: ~a)
register.filter(name='sum')(mapped_filter(sum))
register.filter(name='min')(mapped_filter(min))
register.filter(name='max')(mapped_filter(max))
register.filter(name='pair')(lambda a, b: (a, b))
register.filter(name='get')(lambda a, b: a.get(b))
register.filter(name='getattr')(lambda a, b: getattr(a, b, ''))
register.filter(name='hasattr')(lambda a, b: hasattr(a, b))
register.filter(name='getitem')(lambda a, b: a[b])
register.filter(name='repeat')(lambda a, b: mark_safe(unicode(a) * b))
register.filter(name='range')(lambda n: xrange(n))
register.filter(name='json')(lambda x: simplejson.dumps(x))

class GetvarsNode(template.Node):
    def __init__(self, update=None):
        self.update = update
        
    def render(self, context):
        request = context['request']
        getvars = request.GET.copy()
        update = {}
        for key, exp in self.update:
            if key[-1] == "+":
                key = key[:-1]
            elif key in getvars:
                del getvars[key]
            update[key] = exp.resolve(context)
        getvars.update(update)
        return getvars.urlencode()


@register.tag
def getvars(parser, token):
    bits = token.split_contents()
    update = []
    for bit in bits[1:]:
        name, exp = bit.split("=", 1)
        update.append((name, parser.compile_filter(exp)))
    return GetvarsNode(update)


re_widont = re.compile(r'\s+(\S+\s*)$')
@register.filter
def widont(value, count=1):
    for i in range(count):
        value = re_widont.sub(lambda m: u"\u00A0%s" % m.group(1), force_unicode(value))
    return value


re_widont_html = re.compile(r'([^<>\s])\s+([^<>\s]+\s*)(</?(?:pre|code|address|blockquote|br|dd|div|dt|fieldset|form|h[1-6]|li|noscript|p|td|th)[^>]*>|$)', re.IGNORECASE)
@register.filter
def widont_html(value):
    return re_widont_html.sub(lambda m: u'%s&nbsp;%s%s' % m.groups(), force_unicode(value))


