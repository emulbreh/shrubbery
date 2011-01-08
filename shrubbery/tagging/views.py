import re
from django.shortcuts import get_object_or_404
from django.http import Http404

from shrubbery.tagging.models import Tag, TagQ, get_tags
from shrubbery.tagging.clouds import Cloud
from shrubbery.views import GenericView, ListView
from shrubbery.db.utils import get_query_set

class TaggedListView(ListView):
    def __init__(self, template, queryset, **kwargs):
        self.get_tag_var = kwargs.pop('get_tag_var', 'tags')
        self.get_tag_separator = kwargs.pop('get_tag_separator', ',')
        self.url_tag_var = kwargs.pop('url_tag_var', 'tags')
        self.url_tag_separator = kwargs.pop('url_tag_separator', ',')
        self.implicit_tags = get_tags(kwargs.pop('implicit_tags', set()), create=False)
        super(TaggedListView, self).__init__(template, queryset, **kwargs)

    def get_query_set(self, request):
        qs = super(TaggedListView, self).get_query_set(request)
        tags = self.get_query_tags(request).union(self.implicit_tags)
        if tags:
            qs = qs.complex_filter(TagQ.all(*tags))
        return qs
        
    def smart_split_tags(self, tags):
        if not isinstance(tags, basestring):
            return tags
        result = []
        for tag in tags.split(self.get_tag_separator):
            try:
                result.append(int(tag))
            except ValueError:
                result.append(tag)
        return result

    def get_query_tags(self, request):
        if not hasattr(request, 'tags'):
            get_tag_query = self.smart_split_tags(request.GET.get(self.get_tag_var, ''))
            view_tag_query = self.smart_split_tags(request.view_context.kwargs.get(self.url_tag_var, ''))
            request.tags = get_tags(get_tag_query + view_tag_query, create=False)
        return request.tags
        
    def get_context_dict(self, request):
        context = super(TaggedListView, self).get_context_dict(request)
        qs = context['objects']
        selected_tags = self.get_query_tags(request)
        common_tags = qs.common_tags()
        related_tags = qs.tags().exclude(pk__in=[tag.pk for tag in selected_tags])
        context.update({
            'tags': self.queryset.tags(),
            'selected_tags': selected_tags,
            'related_tags': related_tags,
            'common_tags': common_tags,
            'drilldown_tags': related_tags.exclude(pk__in=common_tags.values('pk').query),
        })
        return context


class TaggedObjectDetailView(GenericView):
    def __init__(self, queryset, pk_var='pk', **kwargs):
        super(TaggedObjectDetailView, self).__init__(**kwargs)
        self.queryset = get_query_set(queryset)
        self.pk_var = pk_var
        self.slug_lookup = 'slug'
        
    def get_object(self, request):
        key = request.view_context.kwargs.get(self.pk_var)
        try:
            lookup = {'pk': int(key)}
        except ValueError:
            lookup = {self.slug_lookup: key}
        obj = get_object_or_404(self.queryset, **lookup)
        slug = getattr(obj, self.slug_lookup, None)
        if slug and key != slug:
            raise Http404
        return obj

    def get_context_dict(self, request):
        context = super(TaggedObjectDetailView, self).get_context_dict(request)
        obj = self.get_object(request)
        context['object'] = obj
        context['tags'] = obj.tags.order_by('name')
        return context


class CloudView(GenericView):
    def __init__(self, queryset, **kwargs):
        self.queryset = get_query_set(queryset)
        super(CloudView, self).__init__(**kwargs)

    def get_query_set(self, request, url):
        return self.queryset
        
    def get_context_dict(self, request):
        context = super(CloudView, self).get_context_dict(request)
        context['cloud'] = Cloud()
        return context