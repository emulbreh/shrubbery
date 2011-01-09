.. include:: _lib/links.rst
.. _index:

=========
shrubbery
=========

shrubbery is a collection of utilities for `django <http://www.djangoproject.com/>`_. It requires django 1.3.

The code is available under the `MIT License <https://github.com/emulbreh/shrubbery/blob/master/LICENSE>`_ `on github <https://github.com/emulbreh/shrubbery/>`_.

It should be compatible with `south`_.

Modules
=======

:ref:`shrubbery.conf <conf>`
    Provides utilities to define app-local settings.


:ref:`shrubbery.db <db>`
    Provides utilities and extensions for django's ORM: :doc:`fields <db/fields>`, :doc:`managers <db/managers>`, :doc:`multiple joins <db/many_related_join>`, 
    :doc:`arbitrary queryset unions <db/union>`, and :doc:`misc utilities <db/utils>`.


:ref:`shrubbery.polymorph <polymorph>`
    Provides generic relations similar to (:ref:`but more powerful than <why_not_contenttypes>`) those in django.contrib.contenttypes_.


:ref:`shrubbery.tagging <tagging>`
    Provides a tagging implementation on top of :ref:`shrubbery.polymorph <polymorph>`.


:ref:`shrubbery.utils <utils>`
    Provides utilities for working with :doc:`text <utils/text>`, :doc:`time <utils/time>`, :doc:`templates <utils/templatetags>`, and :doc:`more <utils/misc>`.


Indices and tables
==================

* :ref:`toc`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 1
   :hidden:
   
   toc