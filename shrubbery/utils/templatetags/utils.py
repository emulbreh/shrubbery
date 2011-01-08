import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def mapped_filter(func):
    def f(value, arg=None):
        if arg:
            try:
                value = [getattr(val, arg, default) for val in value]
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
register.filter(name='getitem')(lambda a, b: a[b])
register.filter(name='repeat')(lambda a, b: mark_safe(unicode(a) * b))

register.filter(name='range')(lambda n: xrange(n))

# Fixme: settings ?
FIRST_PAGES = 3
LAST_PAGES = 3
BEFORE_PAGES = 5
AFTER_PAGES = 5

class PageRange(object):
    def __init__(self, start, stop, ellipsis=False, current=False):
        self.range = xrange(start, stop)
        self.ellipsis = ellipsis
        self.current = current
        
    def __iter__(self):
        return iter(self.range)
        
class PageRanges(object):
    def __init__(self, page, first=3, last=3, before=5, after=5):
        self.page = page
        self.first, self.last = first, last
        self.before, self.after = before, after
        
    def __iter__(self):
        count = self.page.paginator.count
        n = len(self.page.paginator.page_range)
        p = self.page.number
        
        if p - self.beforce <= self.first + 1:
            yield PageRange(1, p)
        else:
            e_start, e_stop = self.first + 1, p - self.before
            yield PageRange(1, e_start)
            yield PageRange(e_start, e_stop, ellipsis=True)
            yield PageRange(e_stop, p)
        
        yield PageRange(p, p + 1, current=True)
        
        if p + 1 + self.after >= n - self.last:
            yield PageRange(p + 1, n + 1)
        else:
            e_start, e_stop = p + 1 + self.after, n - self.last + 1
            yield PageRange(p + 1, e_start)
            yield PageRange(e_start, e_stop, ellipsis=True)
            yield PageRange(e_stop, n + 1)
        
        
@register.inclusion_tag('utils/paginator.html', takes_context=True)
def paginator(context, page):
    inator = page.paginator
    inator.count
    n = len(inator.page_range)
    p = page.number
    intervalls = []
            
    if p - BEFORE_PAGES <= FIRST_PAGES + 1:
        intervalls.append(PageRange(1, p))
    else:
        e_start, e_stop = FIRST_PAGES + 1, p - BEFORE_PAGES
        intervalls.append(PageRange(1, e_start))
        intervalls.append(PageRange(e_start, e_stop, ellipsis=True))
        intervalls.append(PageRange(e_stop, p))
        
    intervalls.append(PageRange(p, p + 1, current=True))        
    
    if p + 1 + AFTER_PAGES >= n - LAST_PAGES:
        intervalls.append(PageRange(p + 1, n + 1))
    else:
        e_start, e_stop = p + 1 + AFTER_PAGES, n - LAST_PAGES + 1
        intervalls.append(PageRange(p + 1, e_start))
        intervalls.append(PageRange(e_start, e_stop, ellipsis=True))
        intervalls.append(PageRange(e_stop, n + 1))
    
    querydict = context['request'].GET.copy()
    if 'page' in querydict:
        del querydict['page']
    return {
        'count_label': context.get('count_label', 'Insgesamt'),
        'paginator': inator,
        'page': page,
        'intervalls': intervalls,
        'querydict': querydict,
    }

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
        name, exp = bits.split("=", 1)
        update.append((name, parser.compile_filter(exp)))
    return GetvarsNode(update)
