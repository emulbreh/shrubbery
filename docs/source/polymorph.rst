.. module:: shrubbery.polymorph

.. include:: _lib/django_doc_links.rst

.. _polymorph:

===================
shrubbery.polymorph
===================
This module provides unique ids accross models that can be used to create efficient generic many-to-many and foreign-key relations similar to those in `django.contrib.contenttypes`_. For a step by step explanation of its motivation and concept, see :ref:`Motivation and Concept <polymorph_motivation>`.
For reasons not to use `django.contrib.contenttypes`_, see :ref:`why_not_contenttypes`

.. code-block:: python

    from shrubbery import polymorph
    from django.db import models
    
    class Post(ObjectModel):
        title = models.CharField(max_length=42)
        ...

.. _polymorph-models:

Models
======

.. class:: Object

    Abstract base class. It defines a `OneToOneField`_ to :class:`ObjectIdentity` as its primary key to ensure its ``pk`` values will be unique across models.

.. attribute:: Object.id

    A primary key ``OneToOneField`` to :class:`ObjectIdentity`

.. method:: Object.save(**kwargs)

    Creates a new :class:`ObjectIdentity` for unsaved instances. Make sure you call ``super().save()`` from subclasses.
    


.. class:: Type

    Type provides functionality similar to `ContentType`_, but it only tracks models that subclass :class:`Object`. 
    It is a subclass of :class:`Object` itself:
    
    .. code-block:: pycon

        >>> tt = Type.objects.get_for_model(Type)
        >>> tt.id.type == tt
        True
    
.. attribute:: Type.name
    
    The name of the corresponding model class.

.. attribute:: Type.module_name

    The name of module defining the corresponding model.

.. attribute:: Type.abstract

    A boolean indicating whether this model is abstract.

.. attribute:: Type.model

    The corresponding model class.

.. attribute:: Type.module

    The module defining the corresponding model.

.. attribute:: Type.app_label

    The app_label of the corresponding model.

.. attribute:: Type.content_type

    Only available if `django.contrib.contenttypes` is installed. The corresponding ContentType instance. This may raise `ContentType.DoesNotExist`.


.. class:: ObjectIdentity

    A simple model that stores a unique id per object as well as its :class:`Type`. Typically you don't create instances explicitly - that is handled by ``Object``'s ``save()`` method.
    

.. attribute:: ObjectIdentity.id

    A globally unique object id


.. attribute:: ObjectIdentity.type
    
    The :class:`Type` for this object.


.. attribute:: ObjectIdentity.instance

    The corresponding ``Object`` instance. Accessing this property potentially hits the DB.


.. method:: ObjectIdentity.coerce(model)

    Tries to return the corresponding ``Object`` instance. If the object is not an instance of ``model``, ``model.DoesNotExist`` will be raised.


.. class:: ObjectManager

    A manager for subclasses of :class:`Object`. It behaves like a plain manager for non-abstract models. But for abstract models, it will be a manager for `ObjectIdentity` for the containing model.



.. method:: ObjectManager.instances(*models)

    This method is only available on :class:`ObjectManager` instances for abstract models. It's a shortcut for ``Object.objects.all().instances(*models)``.


.. class:: ObjectIdentityQuerySet

.. method:: ObjectIdentityQuerySet.coerce(model)

    Returns a `QuerySet`_ for the given model that only contains objects in self. This is typically more efficient than calling::      
        
        model.objects.filter(pk__in=self.values('pk').query)
        
    because it avoids the join with ``ObjectIdentity`` if possible.
    

.. method:: ObjectIdentityQuerySet.instances(*models)

    Returns a :class:`UnionQuerySet` for the given models or querysets ``coerce()``d with instances in self. ``models`` defaults to the list of non-abstract, non-proxy, non-virtual submodels of ``Object``.


.. class:: ObjectIdentityManager

    A manager for ObjectIdentityQuerySet that proxies ``coerce()`` and ``instances()``.


.. _polymorph-relations:

Relations
=========
``polymorph`` provides generic relations to :class:`Object` instances that can be accessed like
like regular `ForeignKey`_ or `ManyToManyField`_ related managers.

.. class:: ManyToManyField(**kwargs)

    A subclass of `ManyToManyField`_ 
    that represents a many-to-many relation to :class:`Object`.

    All regular ``ManyToManyField`` options except ``symmetrical``, ``through`` and ``related_name`` are supported.
    
    .. code-block:: python

        from django.db import models
        from shrubbery import polymorph
        
        class Tag(models.Model):
            name = models.CharField(max_length=42)
            object_set = polymorph.ManyToManyField()
    
    .. code-block:: pycon
    
        >>> foo = Tag.objects.create(name="foo")
        >>> bar = Tag.objects.create(name="bar")
        >>> foo.object_set.add(foo_post, foobar_post)
        >>> foo.object_set.all()
        [<Post: 'foo post'>, <Post: 'foobar post'>]
        >>> bar.object_set.add(bar_post, foobar_post)
        >>> Tag.objects.filter(object_set=bar_post)
        [<Tag: 'bar'>]

    You can use the regular reverse `ManyToManyField`_ lookup API as well as 
    the regular reverse related Manager::

        >>> p = Post.objects.filter(tag__name="django")[0]
        >>> p.tag_set.add(Tag.objects.get_or_create(name="nice"))

    But ``tag.object_set`` will only be be an :class:`Object` manager and the related manager will only 
    return :class:`Object` querysets::

        >>> Tag.objects.filter(object_set=p)


.. class:: ForeignKey(**kwargs)

    A subclass of `ForeignKey`_ that represents a foreign-key relation to :class:`Object`. All regular `ForeignKey`_ options except ``related_name`` are supported.
    
    Example::
    
        class Post(polymorph.Object):
            ...
            
        class Comment(models.Model):
            obj = polymorph.ForeignKey()
            text = models.TextField()
            
        >>> post = Post.objects.create(...)
        >>> c = Comment.objects.create(obj=post, text="...")
        >>> Comment.objects.filter(obj=post)
        [<Post: ...>]
        
.. class:: OneToOneField(**kwargs)

    A subclass of `OneToOneField`_ that represents a one-to-one relation to :class:`Object`. All regular `OneToOneField`_ options except ``related_name`` are supported.

    
.. class:: ReverseField(model, field_name)
    
    Creates a descriptor that can be used to access a :class:`ManyToManyField`, :class:`OneToOneField`, or :class:`ForeignKey` from related :class:`Object` instances.
    
        model
            The model that defines the related field. Either the model class or the model name in model reference syntax.
        
        field_name
            The name of the related field.
    

Example::

    class Post(polymorph.Object):
        title = models.CharField(max_length=255)
        tags = polymorph.ReverseField(Tag, 'object_set')
        comments = polymorph.ReverseField(Comment, 'obj')
        meta_data = polymorph.ReverseField(MetaData, 'obj')


    >>> Post.objects.filter(tags=foo)


.. _polymorph-settings:

Settings
========
App-local settings for :mod:`shrubbery.polymorph`:

OBJECT_IDENTITY_DB_TABLE
    The database table name for :class:`ObjectIdentity`
    
OBJECT_IDENTITY_DB_COLUMN
    The database column name for :attr:`Object.id`
    
