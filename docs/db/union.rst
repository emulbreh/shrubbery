.. module:: shrubbery.db.union
.. include:: ../_lib/links.rst

==================
shrubbery.db.union
==================

This module provides a UnionQuerySet that can be used to query multiple (unrelated) querysets in parallel::

    >>> qs = UnionQuerySet(Foo.objects.all(), Bar.objects.filter(...))
    >>> qs.filter(name__startswith="x")
    [<Foo: x1>, <Foo: x2>, <Bar: x1>, <Bar: x4>, <Bar: x5>]

Reference
=========

.. class:: UnionQuerySet(*querysets)

    `querysets` will be converted with :func:`get_query_set` and thus can be models, managers, or querysets. If an abstract model is given, all direct non-abstract, non-virtual, non-proxy models will be queries instead.

    The following `QuerySet`_ methods are available on :class:UnionQuerySet and will be applied to all querysets: 
    `aggregate`, `all`, `annotate`, `complex_filter`, `dates`, `distinct`, `exclude`, `extra`, `filter`, `latest`, `none`, `order_by`, `reverse`, `select_related`.
    

.. attribute:: UnionQuerySet.querysets

    The list of querysets.

.. attribute:: UnionQuerySet.models

    A set of all models that will be queried.

.. attribute:: UnionQuerySet.queries

    A list of the underlying queries.

.. method:: UnionQuerySet.sort(key=None, reverse=False)

.. method:: UnionQuerySet.order_and_sort_by(attr)

.. method:: UnionQuerySet.coerce(model)

.. method:: UnionQuerySet.get_common_fields(check_type=True, local=True)

    Returns a tuple of all field names that are available on all models. If ``check_type=True``, only fields with compatible database types will be returned.
    If ``local=True``, only local fields will be returned.
    
.. method:: UnionQuerySet.fetch_values(fields=None)

    *Experimental*.

    ``fields`` defaults to ``self.get_common_fields(check_type=True, local=True)``. Executes a single SQL query (using ``UNION``).

.. method:: UnionQuerySet.fetch_objects(fields=None)

    *Experimental*
    
    As :meth:`UnionQuerySet.fetch_values`, but returns deferred model instances. Only ``fields`` will be loaded.


Operators
~~~~~~~~~

``union_queryset & other``
    ``other`` can be a `QuerySet`_ or another :class:`UnionQuerySet`. Returns a :class:`UnionQuerySet` representing the intersection of ``union_queryset`` and ``other``.

``union_queryset | other``
    ``other`` can be a `QuerySet`_ or another :class:`UnionQuerySet`. Returns a :class:`UnionQuerySet` representing the union of ``union_queryset`` and ``other``.

Classmethods
~~~~~~~~~~~~

.. method:: UnionQuerySet.add_proxy(name, aggregate=None)