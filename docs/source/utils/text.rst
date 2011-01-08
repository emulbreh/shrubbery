.. module:: shrubbery.utils.text

.. _utils_text:

====================
shrubbery.utils.text
====================


.. function:: camel_case(s, initial_cap=None)

    Returns a CamelCase version of ``s``. If ``initial_cap`` is ``True`` or ``False`` the first character will be forced to upper- or lower-case respectively.
    
        >>> camel_case('foo_bar_baz')
        'fooBarBaz'
        >>> camel_case('foo_bar_baz', True)
        'FooBarBaz'


.. function:: camel_split(s)

    >>> camel_split("htmlToXml")
    ['html', 'To', 'Xml']
    >>> camel_split("HtmlToXml")
    ['Html', 'To', 'Xml']    
    >>> camel_split("HTMLToXml")
    ['HTML', 'To', 'Xml']
    >>> camel_split("HTMLToXML")
    ['HTML', 'To', 'XML']
    >>> camel_split("htmlToXML")
    ['html', 'To', 'XML']
    