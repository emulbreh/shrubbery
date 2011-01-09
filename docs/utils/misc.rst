.. module:: shrubbery.utils
.. _utils_misc:

===============
shrubbery.utils
===============
   
.. function:: class_property(func)

    A decorator that works like a combination of ``@classmethod`` and ``@property``.

.. function:: cached_property(func)

    Returns a descriptor for a property that will be computed only once (on first access).
    It supports setting the cached value directly as well as deleting the cached value::
    
        >>> class Foo(object):
                @cached_property
                def x(self):
                    print "compute x"
                    return "bar"
        >>> foo = Foo()
        >>> foo.x
        compute x
        bar
        >>> foo.x
        bar
        >>> foo.x = "baz"
        >>> foo.x
        baz
        >>> del foo.x
        >>> foo.x
        compute x
        bar

.. function:: autodiscover(module_name)

    Search ``INSTALLED_APPS`` for apps that contain a module named ``module_name``.
    Returns a dictionary that maps apps to found modules.

.. function:: reduce_or(iterable)

    Equivalent to ``reduce(lambda a, b: a | b, iterable)``.
    
.. function:: reduce_and(iterable)

    Equivalent to ``reduce(lambda a, b: a & b, iterable)``.
    
