.. module:: shrubbery.utils
.. _utils_templatetags:

============================
shrubbery.utils.templatetags
============================
   
Provides a template library called ``shrubbery_utils``.

Filters
=======

concat
    ``lambda a, b: "%s%s" % (a, b))``

contains
    ``lambda a, b: b in a``

in
    ``lambda a, b: a in b``

eq
    ``lambda a, b: a == b``

lt
    ``lambda a, b: a < b``

le
    ``lambda a, b: a <= b``

gt
    ``lambda a, b: a > b``

ge
    ``lambda a, b: a >= b``

add
    ``lambda a, b: a + b``

sub
    ``lambda a, b: a - b``

mul
    ``lambda a, b: a * b``

neg
    ``lambda a: -a``

invert
    ``lambda a: ~a``

pair
    ``lambda a, b: (a, b)``

get
    ``lambda a, b: a.get(b)``

getattr
    ``lambda a, b: getattr(a, b, '')``

getitem
    ``lambda a, b: a[b]``

repeat
    ``lambda a, b: mark_safe(unicode(a) * b)``

range
    ``lambda n: xrange(n)``

sum:[attr]
    ``sum(a)``. If ``attr`` is given: ``sum([getattr(x, attr) for x in a])``.

min:[attr]
    ``min(a)``. If ``attr`` is given: ``min([getattr(x, attr) for x in a])``.

max:[attr]
    ``max(a)``. If ``attr`` is given: ``max([getattr(x, attr) for x in a])``.
    
widont
    joins the last two words of its input with ``'\u00A0'`` (non-breaking space). Django's autoescaping will turn this into ``'&nbsp;'``.

widont_html
    joins the last two words of its input with ``'&nbsp;'`` and leaves html tags intact.

Tags
====

{% getvars %}
~~~~~~~~~~~~~

Requires the `request context processor <http://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-request>`_.

.. code-block:: django
    
    <!-- querystring: foo=1&bar=2 -->
    {% getvars %} will render the querystring as-is: foo=1&bar=2
    {% getvars baz=3 %} will add baz=3: foo=1&bar=2&baz=3
    {% getvars foo=4 %} will replace foo: foo=4&bar=2
    {% getvars foo+=4 %} will add foo=42: foo=1&foo=4&bar=2
    {% getvars foo+=4 bar=5 baz=3 %} will result in foo=1&foo=4&bar=5&baz=3
    
    
