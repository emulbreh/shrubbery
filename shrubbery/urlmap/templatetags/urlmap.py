from django import template
from shrubbery.urlmap import reverse

register = template.Library()

class UrlMapNode(template.Node):
    def __init__(self, obj_expr, use_case):
        self.obj_expr = obj_expr
        self.use_case = use_case
    
    def render(self, context):
        if self.use_case:
            use_case = use_case.resolve(context)
        else:
            use_case = None
        obj = self.obj_expr.resolve(context)
        return reverse(obj, use_case=use_case)
    
@register.tag('urlmap')
def do_urlmap(parser, token):
    bits = token.split_contents()
    if len(bits) not in (2, 3):
        raise template.TemplateSyntaxError("{% urlmap %} requires one or two arguments")
    if len(bits) == 3:
        use_case = parser.compile_filter(bits[2])
    else:
        use_case = None
    obj_expr = parser.compile_filter(bits[1])
    return UrlMapNode(obj_expr, use_case)
    
@register.filter
def urlmap(obj, use_case=None):
    return reverse(obj, use_case=use_case)