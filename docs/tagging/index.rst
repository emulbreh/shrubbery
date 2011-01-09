.. module:: shrubbery.tagging
.. include:: ../_lib/links.rst
.. _tagging:

=================
shrubbery.tagging
=================

Provides tagging utilities on top of :mod:`shrubbery.polymorph`. If you have :ref:`reasons not to use <why_not_django_tagging>` `django-tagging`_.

Models
======

.. module:: shrubbery.tagging.models

.. class:: Tag()

    Can be used as a Q-object.

.. attribute:: Tag.name

    A CharField - its `max_length` can be configured via ``TAG_NAME_MAX_LENGTH``.
    
.. attribute:: Tag.object_set

    A :class:`polymorph.ManyToManyField`.    


.. class:: Tagged()

    An abstract model.

.. attribute:: Tagged.tags

    A :class:`polymorph.ReverseField` for :attr:`Tag.object_set`.
    
.. attribute:: Tagged.objects

    A :class:`TaggedManager`.


.. class:: TaggedQuerySet

.. method:: TaggedQuerySet.tags()

    Returns a queryset of all tags linked to objects in this queryset.

.. method:: TaggeQuerySet.with_similar_tags(obj)

    Returns a queryset containing all instances that have at least one tag in common with ``obj`` ordered by the number of tags in common (descending).


.. class:: TaggedManager()

    A subclass of `ObjectManager` that uses `TaggedQuerySet` and proxies `tags()`.

.. class:: TagQ()

    A :class:`ManyRelatedJoinQ` to use with :class:`Tagged` querysets.    
    

.. class TaggedUnionQuerySet()


Views
=====

.. module:: shrubbery.tagging.views

.. class:: TaggedListView(template, queryset, **kwargs)

    Supports the same arguments as :class:`ListView`. ``queryset`` should be a subset of. Additionally you can pass in:

        ``tag_var = 'tags'``
            The GET variable used to filter the list view by tags. 
    
        ``implicit_tags = ()``
            A collection of tags that will always be included in this query.
        
    Context Variables:

    tags
        A queryset of all tags related to ``self.queryset``.
    
    selected_tags
        A list of the :class:`Tag` objects passed through ``tag_var``.
    
    related_tags
        A queryset of all tags related to the filtered queryset that will be passed to the template.

    common_tags
        A queryset of all tags that are related to all objects in the filtered queryset.

    drilldown_tags
        A queryset of all tags usable to further narrow down the search result.


Settings
========
App local settings for :mod:`shrubbery.tagging`:

TAG_NAME_MAX_LENGTH
    The ``max_length`` for :attr:`Tag.name`.
