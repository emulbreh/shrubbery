import re
from django.core.paginator import QuerySetPaginator
from django.template import loader, RequestContext
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import models
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from shrubbery.db.utils import get_query_set
from shrubbery.utils import reduce_or, reduce_and

DEFAULT_PAGE_SIZE = 30
DEFAULT_PAGE_VAR = 'page'

def render(request, template, context_dict, **kwargs):
    context = RequestContext(request, context_dict)
    if isinstance(template, str):
        template = loader.get_template(template)
    if isinstance(template, (tuple, list)):
        template = loader.select_template(*template)
    return HttpResponse(template.render(context), **kwargs)
    
def redirect_to_next_url(request, default, var='next'):
    url = request.GET.get(var, None)
    if not url or '//' in url:
        url = default
    return HttpResponseRedirect(url)

def paginate(request, queryset, page_size=DEFAULT_PAGE_SIZE, page_var=DEFAULT_PAGE_VAR):
    paginator = Paginator(queryset, page_size)
    try:
        page_num = int(request.GET.get(page_var, 1))
    except ValueError:
        page_num = 1
    try:
        page = paginator.page(page_num)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)
    return page

class ViewContext(object):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs
        self.data = {}
        
class GenericView(object):
    http_methods = ['GET']
    template = None
    
    def __init__(self, template=None, extra_context=None):
        if template:
            self.template = template
        self.extra_context = extra_context or {}

    def get_context_dict(self, request):
        context = {'view': self}
        context.update(self.extra_context)
        return context
        
    def get_template(self, request):
        return self.template
    
    def get_response_kwargs(self, request):
        return {}
        
    def get_response(self, request, context=None, extra_context=None, template=None):
        if not context:
            context = self.get_context_dict(request)
        if extra_context:
            context.update(extra_context)
        if not template:
            template = self.get_template(request)
        return render(request, template, context, **self.get_response_kwargs(request))
    
    def __call__(self, request, *args, **kwargs):
        if not request.method in self.http_methods:
            return HttpResponseNotAllowed(self.http_methods)
        request.view_context = ViewContext(args, kwargs)
        #request.url_args = args
        #request.url_kwargs = kwargs
        return self.get_response(request)
                        
search_term_re = re.compile(r'([-+]?)("(?:(?:\\[\\"])|[^"\\])*"|\S+)')

class ListView(GenericView):
    def __init__(self, template, queryset, **kwargs):        
        self.queryset = get_query_set(queryset)
        self.page_size = kwargs.pop('page_size', DEFAULT_PAGE_SIZE)
        self.page_var = kwargs.pop('page_var', DEFAULT_PAGE_VAR)
        self.searchable = kwargs.pop('searchable', True)
        self.search_var = kwargs.pop('search_var', 'q')
        self.search_fields = kwargs.pop('search_fields', ())
        self.search_lookup = kwargs.pop('search_lookup', 'icontains')
        super(ListView, self).__init__(template, **kwargs)
    
    def get_search_terms(self, query):
        terms = []
        for match in search_term_re.finditer(query):
            op, term = match.group(1), match.group(2)
            if term[0] == '"' and term[0] == term[-1]:
                term = term[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            if term:
                terms.append((term, op == '-'))
        return terms
    
    def get_search_q(self, query):
        terms = self.get_search_terms(query)
        if not terms or not self.search_fields:
            return None
        term_q_objs = []
        for term, negate in terms:
            field_q_objs = []
            for field in self.search_fields:
                q = models.Q(**{"%s__%s" % (field, self.search_lookup): term})
                field_q_objs.append(q)
            term_q = reduce_or(field_q_objs)
            if negate:
                term_q = ~term_q
            term_q_objs.append(term_q)
        return reduce_and(term_q_objs)
    
    def get_query_set(self, request):
        qs = self.queryset.all()
        if self.searchable:            
            query = request.GET.get(self.search_var, '')
            q = self.get_search_q(query)
            if q:
                qs = qs.filter(q)
        return qs
    
    def get_context_dict(self, request):       
        context = super(ListView, self).get_context_dict(request)
        qs = self.get_query_set(request)
        context['page'] = paginate(request, qs, page_var=self.page_var, page_size=self.page_size)
        context['objects'] = qs
        return context
        
 
class FormView(GenericView):
    http_methods = ['GET', 'POST']
    def __init__(self, template, form, success_template=None, redirect=None, redirect_var=None, **kwargs):
        super(FormView, self).__init__(template, **kwargs)
        self.redirect = redirect
        self.redirect_var = redirect_var
        self.success_template = success_template

    def get_instance(self, request):
        return None
        
    def get_success_template(self, request, form):
        return self.success_template
        
    def get_success_context_dict(self, request, form):
        context = super(FormView, self).get_context_dict(request)
        context['form'] = form
        return context

    def get_success_response(self, request, form, template=None, extra_context=None):
        redirect = self.redirect
        if self.redirect_var:
            redirect = request.GET.get(self.redirect_var, redirect)        
        if redirect:
            return HttpResponseRedirect(redirect)
        if not template:
            template = self.get_success_template(request, form)
        context = self.get_success_context_dict(request, form)
        if extra_context:
            context.update(extra_context)
        return super(FormView, self).get_response(request, template=template, context=context)

    def get_response(self, request):        
        form_kwargs = {}
        instance = self.get_instance(request)
        if instance is not None:
            form_kwargs['instance'] = instance
        if request.method == 'POST':
            form = self.form(request.POST, request.FILES, **kwargs)
            if form.is_valid():
                self.handle_valid_form()
                return self.get_success_response(request, form)
        else:
            form = self.form(**kwargs)
        return super(FormView, self).get_response(request, {
            'form': form
        })

        