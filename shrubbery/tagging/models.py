from django.db import models
from shrubbery.tagging.encoding import parse_tags, encode_tags
from shrubbery import polymorph
from shrubbery.db.managers import Manager
from shrubbery.db.many_related_join import ManyRelatedJoinQ
from shrubbery.db.utils import get_sub_models, ImplicitQMixin
from shrubbery.db.union import UnionQuerySet
from shrubbery.utils import reduce_or

##### managers, querysets, and q-objects #####

class TaggedQuerySet(models.query.QuerySet):
    @Manager.proxy_method
    def tags(self):
        return Tag.objects.filter(object_set__in=self).distinct()
        
    @Manager.proxy_method
    def with_similar_tags(self, obj):
        return self.filter(tags__in=obj.tags.all()).annotate(common_tag_count=models.Count('tags')).filter(common_tag_count__gt=0).order_by('-common_tag_count')
        
    @Manager.proxy_method
    def common_tags(self):
        count = self.count()
        return self.tags().annotate(object_count=models.Count('object_set')).filter(object_count=count)
        
    @Manager.proxy_method
    def coverage(self, tags):
        return self.filter(tags__in=tags.values('pk').query).count() / float(self.count())
        
    
class TagFieldManager(Manager):
    def add(self, *tags):
        return super(TagFieldManager, self).add(*[get_tag(tag) for tag in tags])

    def assign(self, tags):
        if isinstance(tags, (str, unicode)):
            tags = parse_tags(tags)
        self.clear()
        self.add(*tags)

    def __unicode__(self):
        return encode_tags(self.all())        
        
TaggedManager = polymorph.ObjectManager.for_queryset(TaggedQuerySet)

class TaggedUnionQuerySet(UnionQuerySet):
    def tags(self):
        return reduce_or(qs.tags() for qs in self.querysets)
        
    def coverage(self, tags):
        tag_pk_query = tags.values('pk').query        
        return sum(qs.filter(tags__in=tag_pk_query).count() for qs in self.querysets) / float(self.count())


##### models #####

class Tag(models.Model, ImplicitQMixin):
    name = models.CharField(max_length = 100, unique=True)
    object_set = polymorph.ManyToManyField()
    
    class Meta:
        ordering = ('name',)
            
    def __unicode__(self):
        return self.name

    def as_q(self):
        return TagQ(self)
        
class TagQ(ManyRelatedJoinQ):
    model = Tag
    field = 'tags'        


class Tagged(polymorph.Object):
    tags = polymorph.ReverseField(Tag, 'object_set', manager_class=TagFieldManager)    
    objects = TaggedManager()
    
    class Meta:
        abstract = True    
    
    def similar_objects(self):
        return UnionQuerySet(TaggedObject).filter(tags__in=self.tags).annotate(common_tag_count=models.Count('tags')).order_by('-common_tag_count')

##### utilities #####

def get_tag(tag, create=False, str_pk=False):
    if isinstance(tag, Tag):
        return tag
    if isinstance(tag, (str, unicode)):
        if str_pk:
            try:
                return Tag.objects.get(pk=int(tag))
            except ValueError:
                pass
        if create:
            tag, created = Tag.objects.get_or_create(name=tag)
            return tag
        else:
            return Tag.objects.get(name=tag)
    if isinstance(tag, (int, long)):
        return Tag.objects.get(pk=tag)
    raise TypeError("Tag, str, unicode, int, or long instance expected")

def get_tags(tags, create=False, str_pk=False):
    if isinstance(tags, (str, unicode)):
        tags = parse_tags(tags)    
    tag_set = set()
    names = set()    
    tag_lookups = set()
    for tag in tags:
        if isinstance(tag, Tag):
            tag_set.add(tag)
            if create and not tag.pk:
                tag.save()
        elif isinstance(tag, basestring):
            try:
                tag_lookups.add(models.Q(pk=int(tag)))
            except ValueError:
                if create:
                    names.add(tag)
                tag_lookups.add(models.Q(name=tag))
        elif isinstance(tag, (int, long)):
            tag_lookups.add(models.Q(pk=tag))
    if tag_lookups:
        for tag in Tag.objects.filter(reduce_or(tag_lookups)):
            tag_set.add(tag)
        for name in names.difference(tag.name for tag in tag_set):
            tag_set.add(Tag.objects.create(name=name))            
    return tag_set
  
