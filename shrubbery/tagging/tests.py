import unittest
from django.db import models, connection
from django.contrib.contenttypes.models import ContentType

from shrubbery.polymorph.models import Object, ObjectIdentity
from shrubbery import polymorph
from shrubbery.db.union import UnionQuerySet
from shrubbery.db.virtual import VirtualModel
from shrubbery.db.managers import Manager
from shrubbery.tagging.models import Tag, Tagged, TagQ
from shrubbery.tagging import clouds
from shrubbery.tagging.cooccurrences import cossim, jaccard
        
class Comment(models.Model):    
    obj = polymorph.ForeignKey()
    text = models.TextField()
    
    def __str__(self):
        return self.text

    
class Post(Tagged):
    title = models.CharField(max_length=100)

    comments = polymorph.ReverseField(Comment, 'obj')
    
    def __str__(self):
        return self.title
        
class Item(Tagged):
    name = models.CharField(max_length=100)
    
    comments = polymorph.ReverseField(Comment, 'obj')
    
    def __str__(self):
        return self.name
        
class Named(models.Model):
    name = models.CharField(max_length=100)

    objects = models.Manager()

    class Meta:
        abstract = True
    
class A(VirtualModel, Named):
    pass
    
class B(A):
    x = models.CharField(max_length=1)
    
class C(A):
    y = models.CharField(max_length=1)


class TaggingTest(unittest.TestCase):
    def assertResultsEqual(self, qs, res, order_by='pk'):
        if order_by:
            if isinstance(qs, UnionQuerySet):
                qs = qs.order_and_sort_by(order_by)
            qs = qs.order_by(order_by)
            res = sorted(res, key=lambda x: getattr(x, order_by))
            self.assertEqual(list(res), list(qs))
        else:
            self.assertEqual(set(res), set(qs))
    
    def get_tags(self, tags):
        return list(Tag.objects.filter(name__in=tags.upper()))
    
    def create_tagged_objects(self, model, name_field, names):
        prefix = model.__name__[0].upper()
        for index, name in enumerate(names):
            obj = model.objects.create(**{name_field: "%s%s_%s" % (prefix, index, name)})
            obj.tags = self.get_tags(name)
            names[index] = obj
        model.objects.create(**{name_field: "%s%s_%s" % (prefix, len(names), 'x')})
    
    def test_m2m(self):
        a, b, c, d, e, f, g, h, x = [Tag.objects.create(name=tag) for tag in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X')]
        
        posts = ['adeh', 'abcdh', 'cbeh', 'afgh', 'ah', 'bcfh']
        self.create_tagged_objects(Post, 'title', posts)
        items = ['acd', 'bcd', 'bc']
        self.create_tagged_objects(Item, 'name', items)

        b_posts = [p for p in posts if "b" in p.title]
        self.assertResultsEqual(Post.objects.filter(tags=b), b_posts)
        self.assertResultsEqual(b.object_set.coerce(Post), b_posts)

        b_items = [i for i in items if "b" in i.name]
        self.assertResultsEqual(Item.objects.filter(tags=b), b_items)
        self.assertResultsEqual(b.object_set.coerce(Item), b_items)
        
        #ids = [obj.id for obj in items + posts]
        #self.assertResultsEqual(Tagged.objects.instances(), items + posts)
        #self.assertResultsEqual(Tagged.objects.all(), ids)

        self.assertResultsEqual(b.object_set.instances(), b_items + b_posts)
        self.assertResultsEqual(Tagged.objects.instances().filter(tags=b), b_items + b_posts)

        b_ids = [obj.id for obj in b_items + b_posts]
        self.assertResultsEqual(b.object_set.all(), b_ids)
        
        self.assertResultsEqual(Object.objects.all(), list(ObjectIdentity.objects.all()))
        
        item_tags = list(set(tag for item in items for tag in self.get_tags(item.name)))
        self.assertResultsEqual(Tag.objects.filter(object_set__type=polymorph.Type.objects.get_for_model(Item)).distinct(), item_tags)
        self.assertResultsEqual(Item.objects.tags(), item_tags)
        
        #post_tags = list(set(tag for item in items for tag in self.get_tags(item.name)))        
        #self.assertResultsEqual(Tag.objects.filter(object_set__isnull=False).distinct(), list(set(item_tags) | set(post_tags)))
        
        id_count = ObjectIdentity.objects.count()
        p = Post.objects.create(title="foo")
        self.assertEquals(ObjectIdentity.objects.count(), id_count + 1)
        p.delete()
        self.assertEquals(ObjectIdentity.objects.count(), id_count)        
        for i in range(10):
            Post.objects.create(title="foo_%s" % i)
        Post.objects.filter(title__startswith="foo").delete()
        self.assertEquals(ObjectIdentity.objects.count(), id_count)

        post_matches = [p for p in posts if ("b" in p.title and "d" in p.title) or ("b" in p.title and "e" in p.title)]
        self.assertResultsEqual(Post.objects.complex_filter((b & d) | (b & e)).distinct(), post_matches)
                
        cl = clouds.Cloud(queryset=Post, annotations={
            #'lin': cloud.Annotation.LINEAR(), 
            'count': clouds.Annotation.COUNT(), 
            'log': clouds.Annotation.LOGARITHMIC(steps=range(1,4)),
        })
        print cl
        print cl.kmeans(3)
        print cl.cache_key
        
        for t in Tag.objects.all():
            print b, t, cossim(b, t, Post), jaccard(b, t, Post)
        
        print Post.objects.tags()
        print Item.objects.tags()
        print Tag.objects.all()
        print Tag.objects.exclude(object_set=None)
        print Post.objects.complex_filter(a & ~a)
        print Post.objects.complex_filter(a | ~a)
        
        print str(a.object_set.coerce(Item).query)
        print a.object_set.coerce(Item)
        
