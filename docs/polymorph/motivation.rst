.. include:: ../_lib/links.rst

.. _polymorph_motivation:

=============================================
shrubbery.polymorph -- Motivation and Concept
=============================================

Assume you have two models - ``Foo`` and ``Bar`` - that you want to tag with ``Tag`` objects. And you want to

* query both models directly: ``Foo.objects.filter(tags__name="TAG")``,
* calculate the total number of tag uses (across ``Foo`` and ``Bar``) to display a tag-cloud, 
* avoid writing raw SQL,
* avoid using django-tagging_ for :ref:`some reason <why_not_django_tagging>`,
* avoid using `django.contrib.contenttypes`_ for :ref:`a similar reason <why_not_contenttypes>`,
* avoid patching django (as `contenttypes` does).

The following code samples will not always actually work, as implementation details are left out. The last iteration however, will be fully functional.

Iteration I
===========

The simplest approach: use a plain `ManyToManyField`_.

.. code-block:: python

    class Tag(models.Model):
        name = models.CharField(max_length=100)
    
    class Foo(models.Model):
        tags = models.ManyToManyField(Tag)
    
    class Bar(models.Model):
        tags = models.ManyToManyField(Tag)
        

Now every tagged model creates its own intermediary table.
As a consequence, getting the total number of tag uses is hard::

    tags = Tag.objects.annotate(foo_count=models.Count('foo_set'))
    tags = tags.annotate(bar_count=models.Count('bar_set'))
    for tag in tags:
        print tag, tag.foo_count + tag.bar_count
        
You'd need to somehow know all tagged models and it requires a join (or a query) per model.
    
Iteration II
============

If we want to store all relations to ``Tag`` in a single table, we'll need a way to distinguish relations from ``Foo(pk=1)`` and ``Bar(pk=1)``.
`django-tagging`_ solves this by introducing a discriminator column on the intermediary table (via `django.contrib.contenttypes`_), but that makes queries harder to write and read.

If we can guarantee that all tagged instances have a unique ``pk`` value, we can do without a discriminator column and directly join through the intermediary table.
This is possible if all models that shall use the relation share a non-abstract base class:

.. code-block:: python

    class ObjectIdentity(models.Model):
        pass

    class Tag(models.Model):
        name = models.CharField(max_length=100)
        object_set = models.ManyToManyField(Object, related_name="tags")
    
    class Foo(ObjectIdentity): pass
    
    class Bar(ObjectIdentity): pass

Now there's only one intermediary table and we can get the total number of tag uses easyly::
    
    for tag in Tag.objects.annotate(count=models.Count('object_set')):
        print tag, tag.count
    
But any query for ``Foo`` objects will join ``ObjectIdentity``. Even if you defer all fields of the base class, django will join the parent table.


Creating and deleting ``Foo`` instances will now (and in all further iterations) be slower, but we'll trade this for faster ``SELECT`` queries.


Iteration III
=============

The problem in the previous iteration is multi table inheritance. You can't have it without the extra joins. So we'll emulate this feature with a `OneToOneField`_.

Since ``ObjectIdentity`` requires no arguments it can be auto-created in ``Foo.save()`` and ``Bar.save()`` for new objects - this code is left out for brevity.

.. code-block:: python

    class ObjectIdentity(models.Model):
        pass
        
    class Object(models.Model):
        identity = models.OneToOneField(ObjectIdentity, primary_key=True, related_name="%(class)s_instance")

        class Meta:
            abstract = True

    class Tag(models.Model):
        name = models.CharField(max_length=100)
        object_set = models.ManyToManyField(ObjectIdentity, related_name="tags")

    class Foo(Object): pass

    class Bar(Object): pass

We can still use ``Tag.*.annotate(count=models.Count('object_set'))`` and ``Foo.*.all()`` won't join ``Object`` anymore. 

But ``Foo.*.filter(identity__tags__name="TAG")`` still joins ``Object`` - and we have a readability regression: we don't want ``identity__*``.


Iteration IV
============

Essentially, we want a `ManyToManyField`_ from ``Foo`` to ``Tag`` that uses the ``Tag.object_set`` table. We can do this with a ``through`` model that uses the same ``Meta.db_table`` and has ``Meta.manged=False``.

.. code-block:: python

    class ObjectIdentity(models.Model):
        pass

    class Object(models.Model):
        identity = models.OneToOneField(ObjectIdentity, primary_key=True, related_name="%(class)s_instance")

        class Meta:
            abstract = True

    class Tag(models.Model):
        name = models.CharField(max_length=100)
        object_set = models.ManyToManyField(ObjectIdentity, related_name="tags", through='ObjectTagRel')

    class Foo(Object):
        tags = models.ManyToManyField(Tag, through="FooTagRel")

    class Bar(Object):
        tags = models.ManyToManyField(Tag, through="BarTagRel")

    class ObjectTagRel(models.Model):
        object = models.ForeignKey(ObjectIdentity)
        tag = models.ForeignKey(Tag)

        class Meta:
            db_table = 'object_tag'
    
    class FooTagRel(models.Model):
        object = models.ForeignKey(Foo)
        tag = models.ForeignKey(Tag)
    
        class Meta:
            db_table = 'object_tag'
            managed = False
    
    class BarTagRel(models.Model):
        object = models.ForeignKey(Bar)
        tag = models.ForeignKey(Tag)

        class Meta:
            db_table = 'object_tag'
            managed = False

Now, ``Foo.*.all()`` as well as ``Foo.*.filter(tags__name="TAG")`` work without additional joins.

But we have written lots of boilerplate code to support only two relations to ``Tag``.
 
Iteration V
===========

:mod:`shrubbery.polymorph` solves this last problem: it allows you to use the pattern in the last iteration without writing lots of boilerplate code:

.. code-block:: python

    class Tag(models.Model):
        name = models.CharField(max_length=100)
        object_set = polymorph.ManyToManyField()
    
    class Foo(polymorph.models.Object):
        tags = polymorph.ReverseField(Tag, 'object_set')
    
    class Bar(polymorph.models.Object):
        tags = polymorph.ReverseField(Tag, 'object_set')

:class:`ObjectIdentity` also stores the :class:`Type <shrubbery.polymorph.Type>` of instances and thus allows you to get the corresponding :class:`Object <shrubbery.polymorph.models.Object>` instance. :class:`Type` is an equivalent of `ContentType`_ (you can get the corresponding `ContentType`_ through :attr:`Type.content_type <shrubbery.polymorph.Type.content_type>`) but is a subclass of :class:`Object` itself. This is useful if you need polymorph relations to models, e.g. in authorization code.

Given a `QuerySet`_ like ``objects = Tag.objects.get(name="TAG").object_set.all()`` you could get all matching ``Foo`` instances with something like ``Foo.objects.filter(pk__in=objects.values('pk').query)``. But that forces an unnecessary join with :class:`ObjectIdentity` when we could just replace the :class:`ObjectIdentity` table with the ``Foo`` table. You can do this with :meth:`objects.coerce(Foo) <shrubbery.polymorph.models.ObjectIdentityQuerySet.coerce>``.


