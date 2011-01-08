import unittest
from django.db import models
from shrubbery.db.many_related_join import ManyRelatedJoinQ
from shrubbery.db.utils import ImplicitQMixin

class Named(models.Model):
    name = models.CharField(max_length=42)
    
    class Meta:
        abstract = True
        app_label = "db"

    def __unicode__(self):
        return self.name

class FooTag(ImplicitQMixin, Named):
    def as_q(self):
        return FooTagQ(self)

class Foo(Named):
    tags = models.ManyToManyField(FooTag)
    
class FooTagQ(ManyRelatedJoinQ):
    model = FooTag
    field = "tags"    


class Bar(Named): pass

class BarTag(Named):
    bar = models.ForeignKey(Bar, related_name="tags")
    
    def as_q(self):
        return BarTagQ(self)
    
class BarTagQ(ManyRelatedJoinQ):
    model = BarTag
    field = "tags"

from django.db.models.sql.aggregates import Aggregate as SqlAggregate
from django.db.models import Aggregate

class JoinedStringAggSqlite(SqlAggregate):
    sql_function = 'GROUP_CONCAT'
    sql_template = '%(function)s(%(field)s, %(separator)s)'
    
class GroupConcat(Aggregate):
    name = "GroupConcat"
    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = JoinedStringAggSqlite(col, source=models.Field(), is_summary=is_summary, **self.extra)
        query.aggregates[alias] = aggregate
        

class ManyRelatedJoinTest(unittest.TestCase):
    def test_m2m(self):
        a, b, c, d = [FooTag.objects.create(name=x) for x in "ABCD"]        
        for name in ("AB", "ABC", "BC", "AC", "A", "B", "", "D", "CD"):
            foo = Foo.objects.create(name="foo_%s" % name)
            for t in name:
                if t in "ABCDEFG":
                    tag, _ = FooTag.objects.get_or_create(name=t)
                    foo.tags.add(tag)

        foo_a = set(Foo.objects.filter(name__contains="A"))
        foo_b = set(Foo.objects.filter(name__contains="B"))
        foo_all = set(Foo.objects.all())
        q = FooTagQ(a) & FooTagQ(b)
        def foo_tag_filter(arg):
            return set(Foo.objects.complex_filter(arg))

        foos = Foo.objects.all().annotate(tag_pks=GroupConcat('tags__pk', separator='","'))
        print str(foos.query)
        tag_pks = set()
        for foo in foos:
            if not foo.tag_pks:
                foo.tag_pks = []
            else:
                foo.tag_pks = [int(pk) for pk in foo.tag_pks.split(',')]
                tag_pks.update(foo.tag_pks)
        foo_tags = FooTag.objects.in_bulk(list(tag_pks))
        for foo in foos:
            foo.tag_list = [foo_tags[pk] for pk in foo.tag_pks]
        for foo in foos:
            print foo.tag_list
        

        self.failUnlessEqual(foo_tag_filter(q), foo_a.intersection(foo_b))
        self.failUnlessEqual(foo_tag_filter(FooTagQ.all(a, b, c)), set([Foo.objects.get(name__icontains="abc")]))
        self.failUnlessEqual(foo_tag_filter(FooTagQ.any(a, b)), foo_a.union(foo_b))
        self.failUnlessEqual(foo_tag_filter(FooTagQ(a) | ~FooTagQ(a)), foo_all)
        self.failUnlessEqual(foo_tag_filter(FooTagQ(a) & ~FooTagQ(a)), set())
        self.failUnlessEqual(foo_tag_filter(~FooTagQ(a)), foo_all.difference(foo_a))
        self.failUnlessEqual(foo_tag_filter(FooTagQ(a) & ~FooTagQ(b)), foo_a.difference(foo_b))

        self.failIf(Foo.objects.complex_filter(FooTagQ(a) & ~FooTagQ(a)).exists())
        
        self.failUnlessEqual(repr(~(a | b & c)), "(~A) & (~B | ~C)")
        self.failUnlessEqual(repr((a & b) | (c & d)), "(A | C) & (A | D) & (B | C) & (B | D)")
        self.failUnlessEqual(repr((~a & b) | (a & ~b)), "(A | B) & (~A | ~B)")
        self.failUnlessEqual(repr(~~(a & b & c)), "(A) & (B) & (C)")
        self.failUnlessEqual(repr(~a | a), "true")
        self.failUnlessEqual(repr(a & (~a | b)), "(A) & (B)")
        #print repr((a & ((~a|c) & (~c | b))))
        #print repr((a|b) & (~a | ~b))
        #print repr((a|b) & (c | (~a & ~b)))
        #print a | b | c < a | b
        #print a | b < a | b | c        

        #print (a & b & c & d).get_prefix_notation()
        #print ((~a & b) | (a & ~b)).get_prefix_notation()

        