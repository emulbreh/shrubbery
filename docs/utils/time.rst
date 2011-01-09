.. module:: shrubbery.utils.time
.. include:: ../_lib/links.rst
.. _utils_time:

====================
shrubbery.utils.time
====================


.. function:: get_date(obj)

    Returns a ``datetime.date`` object for a given ``date`` or ``datetime`` instance.
    
.. function:: get_first_day_of_week()

    Returns the index of the first day of the week.
    
.. function:: get_week_number(date)

    Returns the week number for a ``datetime.date`` or ``datetime.datetime`` object.
    
.. function:: get_week_range(date)

    Returns ``(first_day, last_day)`` where ``first_day`` and ``last_day`` are ``datetime.date`` objects for the first and last day in the week that ``get_date(date)`` lies in.
    
.. function:: get_month_range(date)
    
    Returns ``(first_day, last_day)`` where ``first_day`` and ``last_day`` are ``datetime.date`` objects for the first and last day in the month that ``get_date(date)`` lies in.
    
.. function:: get_date_or_404(year, month, day)
    
    Returns a ``datetime.date`` object for the given arguments. Raises `Http404`_ if the date would be invalid.
    
