import unittest
from django.db import models

from shrubbery.db.fields.reverse import ReverseDictField, ReverseListField, ListField, ManyToManyList

class TestModel(models.Model):
    class Meta:
        abstract = True
        app_label = "db"

class A(TestModel):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class B(TestModel):
    name = models.CharField(max_length=30)
    a_set = ManyToManyList(A)

    def __str__(self):
        return self.name

class Attrib(TestModel):
    b = ReverseDictField('B', key='key', value='value', related_name='attribs')
    key = models.CharField(max_length=30)
    value = models.CharField(max_length=30)
    
    def __str__(self):
        return 'attribute of %s key=%s value=%s' % (self.b, self.key, self.value)

class AttribType(TestModel):
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name
    
class TypedAttrib(TestModel):
    b = ReverseDictField('B', key='type', value='value', related_name='tattribs')
    type = models.ForeignKey(AttribType)
    value = models.CharField(max_length=10)

class CharSequence(TestModel):
    b = ReverseListField('B', index='index', value='value', related_name='seq')
    index = models.PositiveIntegerField()
    value = models.CharField(max_length=30)
    
class AbRel(TestModel):
    a = models.ForeignKey('AModelWithSeq')
    b = models.ForeignKey('B')
    index = models.PositiveIntegerField()

class AModelWithSeq(TestModel):
    b_objects = models.ManyToManyField(B, through=AbRel, related_name='a_objects')
    seq = ListField(B, related_name='a_list_reverse') 

class Item(TestModel):
    name = models.CharField(max_length=30)

class L(TestModel):
    items = ListField(Item, related_name='lists')
    
class X(TestModel):
    nums = ListField(models.IntegerField())
    

def check_list(manager, seq):
    return [x.index for x in manager.all()] == range(len(seq)) and list(manager) == seq
    
def check_dict(manager, d):
    return dict(manager) == d

class ReverseFieldTest(unittest.TestCase):
    def test_reverse_dict(self):
        b = B.objects.create(name='b1')
        self.failUnless(check_dict(b.attribs, {}))
        
        b.attribs['foo'] = 'bar'
        b.attribs['x'] = 'y'
        self.failUnless(check_dict(b.attribs, {'foo': 'bar', 'x': 'y'}))
        
        b.attribs['foo'] = 'baz'
        self.failUnless(check_dict(b.attribs, {'foo': 'baz', 'x': 'y'}))

        del b.attribs['x']
        self.failUnless(check_dict(b.attribs, {'foo': 'baz'}))
        
        t1 = AttribType.objects.create(name='k1')
        b.tattribs[t1] = 'v1'
        self.failUnless(check_dict(b.tattribs, {t1: 'v1'}))
        
        b.attribs = {'aaa': 'bbb'}
        self.failUnless(check_dict(b.attribs, {'aaa': 'bbb'}))
        
        self.failUnless(b.attribs.pop('aaa') == 'bbb')
        self.failUnless(check_dict(b.attribs, {}))
        
        b2 = B.objects.create(name='b2')
        b2.attribs['x'] = '123'
        self.failUnless(check_dict(b2.attribs, {'x': '123'}))
        self.failUnless(check_dict(b.attribs, {}))
        
        b.attribs['x'] = '123'
        b2.attribs.clear()
        self.failUnless(check_dict(b.attribs, {'x': '123'}))
        self.failUnless(check_dict(b2.attribs, {}))
        
                
    def test_reverse_list(self):            
        b = B.objects.create(name='b2')         
        self.failUnless(check_list(b.seq, []))
        
        b.seq.append("a")
        b.seq.append("b")
        self.failUnless(check_list(b.seq, ["a", "b"]))
        
        b.seq.append("d")
        self.failUnless(check_list(b.seq, ["a", "b", "d"]))

        b.seq[2] = "c"
        self.failUnless(check_list(b.seq, ["a", "b", "c"]))
        
        del b.seq[0]
        self.failUnless(check_list(b.seq, ["b", "c"]))
        
        b.seq.insert(0, "a")
        self.failUnless(check_list(b.seq, ["a", "b", "c"]))
        
        b.seq.extend(["b", "e"])
        self.failUnless(check_list(b.seq, ["a", "b", "c", "b", "e"]))

        index = b.seq.index("b")
        self.failUnless(index == 1)
        
        b.seq.remove("b")
        self.failUnless(check_list(b.seq, ["a", "c", "b", "e"]))
        
        b.seq.insert(1, "b")
        self.failUnless(check_list(b.seq, ["a", "b", "c", "b", "e"]))
        
        self.failUnless(b.seq.count("b") == 2)
        self.failUnless(b.seq.count() == 5)
        self.failUnless(len(b.seq) == 5)
        
        self.failUnless("c" in b.seq)       
        self.failUnless("x" not in b.seq)
        
        self.failUnless(bool(b.seq))
        
        b.seq = []
        self.failUnless(check_list(b.seq, []))      
        self.failUnless(not bool(b.seq))
        
        b.seq = ["a", "b", "c", "d"]
        self.failUnless(check_list(b.seq, ["a", "b", "c", "d"]))
        
        self.failUnless(b.seq[1:] == ["b", "c", "d"])       
        self.failUnless(b.seq[:-1] == ["a", "b", "c"])
        self.failUnless(b.seq[1:-1] == ["b", "c"])
        self.failUnless(b.seq[1:2] == ["b"])
        self.failUnless(b.seq[::-1] == ["d", "c", "b", "a"])
        self.failUnless(b.seq[:] == ["a", "b", "c", "d"])
        
        b.seq[-1:] = ["z"]
        self.failUnless(check_list(b.seq, ["a", "b", "c", "z"]))
        b.seq[1:-1] = ["x", "y"]
        self.failUnless(check_list(b.seq, ["a", "x", "y", "z"]))
        del b.seq[:1]
        self.failUnless(check_list(b.seq, ["x", "y", "z"]))
        
        b.seq = reversed(list(b.seq))        
        self.failUnless(check_list(b.seq, ["z", "y", "x"]))
        b.seq.sort()
        self.failUnless(check_list(b.seq, ["x", "y", "z"]))
        
    def test_m2m_list(self):
        b1 = B.objects.create(name='b1')
        b2 = B.objects.create(name='b2')
        a = AModelWithSeq.objects.create()
        a.seq.append(b1)
        a.seq.append(b2)
        a.seq = [b1]
        
        qs = a.seq.filter(value__name__icontains='1')
        
        b = B.objects.create(name="x")
        b.a_list.append(A.objects.create(name="foo"))
        b.a_list.insert(0, A.objects.create(name="bar"))
        
        
        
        