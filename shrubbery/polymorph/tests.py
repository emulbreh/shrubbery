from django.test import TestCase
from django.db import models, connection
from django.conf import settings

from shrubbery.polymorph.models import Object, ObjectIdentity
from shrubbery import polymorph
from shrubbery.db.union import UnionQuerySet

class Tag(models.Model):
    name = models.CharField(max_length=100)
    object_set = polymorph.ManyToManyField()
    
class Tagged(polymorph.Object):
    tags = polymorph.ReverseField(Tag, 'object_set')
    
    class Meta:
        abstract = True
        
class Comment(models.Model):    
    obj = polymorph.ForeignKey()
    text = models.TextField()
    
    def __str__(self):
        return self.text

class MetaData(models.Model):
    obj = polymorph.OneToOneField()
    value = models.CharField(max_length=100)
    
class Note(models.Model):
    object_set = polymorph.ManyToManyField(db_table='x_note')

    
class Post(Tagged):
    title = models.CharField(max_length=100)
    meta_data = polymorph.ReverseField(MetaData, 'obj')
    comments = polymorph.ReverseField(Comment, 'obj')
    
    def __str__(self):
        return self.title
        
class Item(Tagged):
    name = models.CharField(max_length=100)
    
    comments = polymorph.ReverseField('Comment', 'obj')
    
    def __str__(self):
        return self.name

class Named(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True
        
class A(polymorph.Object):
    name = models.CharField(max_length=100)
    
class B(A):
    pass
    
class C(B):
    pass

class PolymorphTest(TestCase):
    def tearDown(self):
        super(PolymorphTest, self).tearDown()
        polymorph.models.Type.objects.clear_cache()
        
    def assertResultsEqual(self, qs, res, order_by='pk'):
        if order_by:
            if isinstance(qs, UnionQuerySet):
                qs = qs.order_and_sort_by(order_by)
            qs = qs.order_by(order_by)
            res = sorted(res, key=lambda x: getattr(x, order_by))
            self.assertEqual(list(qs), list(res))
        else:
            self.assertEqual(set(qs), set(res))
    
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
        self.assertResultsEqual(items[0].tags.all(), [a, c, d])

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

        #print Tagged.objects.coerce(Post)
        #print Post.identities.all()
        #print Post.objects.instances()
        
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
        #self.assertResultsEqual(Post.objects.complex_filter((b & d) | (b & e)).distinct(), post_matches)
        
    def test_fk(self):
        p1, p2, p3, p4, p5, p6, p7 = [Post.objects.create(title="P%s" % i) for i in range(1, 8)]
        i1, i2, i3 = [Item.objects.create(name="I%s" % i) for i in range(1, 4)]

        p1.comments.add(Comment(text="c1"))
        c = Comment.objects.get(text="c1")
        self.assertEqual(c.obj, p1.id)

        p2.comments.create(text="c2")
        i1.comments.create(text="c3")
        Comment.objects.create(text="c4", obj=i1)
        Comment.objects.create(text="c5", obj=p3)
        
        self.assertResultsEqual(Comment.objects.filter(obj__in=(p1, i1)), list(Comment.objects.filter(text__in=['c1', 'c3', 'c4'])))
        
        commentCount = Comment.objects.count()
        p1CommentCount = p1.comments.count()
        p1.delete()
        self.assertEqual(Comment.objects.count(), commentCount - p1CommentCount)
        
    def test_o2o(self):
        p = Post.objects.create(title="with meta")
        m = MetaData.objects.create(obj=p, value="has meta")
        self.assertEqual(m.obj.instance, p)
        self.assertEqual(p.meta_data, m)
        self.assertResultsEqual(MetaData.objects.filter(obj=p), [m])

    def test_inheritance(self):
        a = A.objects.create(name="a")
        b = B.objects.create(name="b")
        c = C.objects.create(name="c")
        
        
