.. module:: shrubbery.db.fields

.. include:: ../_lib/links.rst

===================
shrubbery.db.fields
===================

Abstract fields
===============

.. class:: VirtualField(**kwargs)

    Takes the same ``kwargs`` as `Field`_. Registers itself as a virtual field for the containing model.
    
.. method:: VirtualField.class_prepared(cls)

    Callback for the containing models `class_prepared`_ signal. 

Lists and Dicts
===============
.. class:: ListField(value_field, **kwargs)

    A :class:`VirtualField`. ``value_field`` can be a `Field`_ instance, model or string. In the latter cases, it is treated as a `ForeignKey`_ to ``value_field``.
    
    ``value_field_name='value'``
        The name used for ``value_field`` on the created list model.
        
    ``index_field_name='index'``
        The name used for the index field on the created list model.


.. class:: ListManager()

    A manager for reverse `ForeignKey`_ descriptors.
    
    Supports the following :class:`list` methods: :meth:`__contains__`, :meth:`__nonzero__`, :meth:`__getitem__`, :meth:`__setitem__`, :meth:`__iter__`, :meth:`__setitem__`, :meth:`__delitem__`, :meth:`insert`, :meth:`append`, :meth:`extend`, :meth:`sort`, :meth:`index`, :meth:`pop`.
    
.. method:: ListManager.count(x)

    If ``x`` is not given, behaves like :meth:`Manager.count`. Else, behaves like :meth:`list.count`
    
.. method:: ListManager.reverse()

    Behaves like a list method, not like :meth:`Manager.reverse`.
    
.. method:: ListManager.remove(x)

    Behaves like a list method, not like a related manager's method.


.. class:: ManyToManyList(to, **kwargs)

    A `ManyToManyField`_ (supports the same ``kwargs`` except ``through``). Creates an intermediary model with an index field and a descriptor on the containing model, whose values are ``to`` instances.
    
    Slicing the list descriptor returns `QuerySets`_ instead of lists.

    ``list_descriptor``
        The name of the list manager descriptor. Defaults to "{field_name}_list". A trailing "_set" will be stripped from the field's name.
    
    ``value_field_name='value'``
        The name used for ``value_field`` on the created list model.

    ``index_field_name='index'``
        The name used for the index field on the created list model.


.. class:: DictField(key_field, value_field, **kwargs)

    A :class:`VirtualField`.

    ``key_field_name='key'``
        The name used for ``key_field`` on the created list model.

    ``value_field_name='value'``
        The name used for ``value_field`` on the created list model.


.. module:: shrubbery.db.fields.reverse

.. class:: ReverseListField()

.. class:: ReverseDictField()


    