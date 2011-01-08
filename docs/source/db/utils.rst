.. module:: shrubbery.db.utils

.. include:: ../_lib/django_doc_links.rst

==================
shrubbery.db.utils
==================

Functions
=========

Argument conversion
~~~~~~~~~~~~~~~~~~~

Library functions sometimes want to accept more argument types than absolutely required (eg. `get_object_or_404`_ which accepts a QuerySet, Manager or Model).
The following functions help dealing with model related arguments.


.. function:: get_q(obj)
    
    If obj is a dict, returns ``Q(**obj)``.
    If obj is a Q-object (or Q-like-object), returns obj.
    If obj has an ``as_q()`` method, returns ``obj.as_q()``.
    Else, raises ValueError.

.. function:: get_model(obj, allow_import=False)

    Returns the model class for a given model instance, queryset, manager, or model.
    If allow_import=True and obj is a string, tries to
    Else, raises ValueError.

.. function:: get_query_set(obj)

    Returns a queryset for a given model, manager or queryset. Uses the default manager for models.
    If obj has a ``get_query_set()`` method, returns ``obj.get_query_set()``.
    Else, raises ValueError.

.. function:: get_manager(obj)

    Returns a manager for a given manager or model. Uses the default manager for models.


Query utilities
~~~~~~~~~~~~~~~

.. function:: force_empty(query)

    Forces the query to return no results. This is hackish, but the only way a Q-like object can force the query set to be empty.

.. function:: remove_join(query, alias, traceless=False)

    Removes the join from `query.join_map`, `query.alias_map`, and `query.rev_join_map`.
    If `traceless=True`, removes it from `query.tables` and `query.alias_refcount` as well.

.. function:: forge_join(query, table, alias, lhs, lhs_alias, lhs_col, col, nullable=False, join_type=None)

    Updates `query.join_map`, `query.alias_map`, and `query.rev_join_map`. 
    This can be used to replace an existing join or to create a new join.

.. function:: replace_text(pattern, replacement, model)


Misc utilities
~~~~~~~~~~~~~~

.. function:: get_sub_models(model, abstract=False, proxy=False, virtual=False, direct=False)

.. function:: unordered_pairs(qs)

    A generator.

.. function:: create_intermediate_model(cls, rel_name, attrs, bases=(models.Model,), meta=None)

.. function:: no_related_name()


Classes
=======

.. class:: ImplicitQMixin()

.. method:: ImplicitQMixin.as_q()

.. method:: ImplicitQMixin.add_to_query(query, aliases=None)

.. method:: ImplicitQMixin.__and__(other)

.. method:: ImplicitQMixin.__or__(other)

.. method:: ImplicitQMixin.__invert__(other)
    