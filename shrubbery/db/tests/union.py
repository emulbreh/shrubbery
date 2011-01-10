from unittest import TestCase

from django.db import models, connection
from django.conf import settings

from shrubbery.db.union import UnionQuerySet

class UABC(models.Model):
    abc = models.CharField(max_length=42)
    
    def __unicode__(self):
        return self.abc
    
    class Meta:
        abstract = True        
        app_label = 'db'
    
class UA(UABC):
    a = models.CharField(max_length=42)
    
    def __unicode__(self):
        return super(UA, self).__unicode__() + ', %s' % self.a
    
class UB(UABC):
    a = models.CharField(max_length=42)
    b = models.CharField(max_length=42)

    def __unicode__(self):    
        return super(UB, self).__unicode__() + ', %s, %s' % (self.a, self.b)

class UC(UABC):
    a = models.CharField(max_length=42)
    b = models.CharField(max_length=42)
    c = models.CharField(max_length=42)    

    def __unicode__(self):    
        return super(UC, self).__unicode__() + ', %s, %s, %s' % (self.a, self.b, self.c)
    

class UnionTest(TestCase):
    def test(self):
        ua = UA.objects.create(abc="abc1", a="a1")
        ub = UB.objects.create(abc="abc2", a="a2", b="b2")
        uc = UC.objects.create(abc="abc3", a="a3", b="b3", c="c3")
        settings.DEBUG = True
        u = UnionQuerySet(UABC)

        #self.failUnlessEqual([obj.pk for obj in u.fetch_objects()], [ua.pk, ub.pk, uc.pk])
        self.failUnlessEqual(list(u), [ua, ub, uc])
        self.failUnlessEqual(list(u[1:]), [ub, uc])
        self.failUnlessEqual(list(u[:2]), [ua, ub])
        self.failUnlessEqual(list(u[1:2]), [ub])

        self.failUnlessEqual(u[0], ua)
        self.failUnlessEqual(u[1], ub)
        self.failUnlessEqual(u[2], uc)
        self.assertRaises(IndexError, u.__getitem__, 3)

        self.failUnlessEqual(list(u.values('a')), [{'a': u'a1'}, {'a': u'a2'}, {'a': u'a3'}])
        self.failUnlessEqual(list(u.coerce(UA)), [ua])
        
        print u.sort('pk')
        print u.sort('pk')[:2]
        print u.sort('-pk')
        
        u = UnionQuerySet(UA, UB, UA.objects.filter(a__contains="a"))
        print u
        
        
        
        