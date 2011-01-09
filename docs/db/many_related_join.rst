.. module:: shrubbery.db.many_related_join

==============================
shrubbery.db.many_related_join
==============================


.. class:: ManyRelatedJoinQ(obj=None)

    Custom Q-object.
    Objects of this class store a boolean expression of `lookup=value` terms in conjunctive normal form. When applied to a query, each disjunction will result in a separate join.
    
Operators
~~~~~~~~~
        
    a & b
        a *and* b
    
    a | b
        a *or* b
        
    ~a
        *not* a
        
    a < b
        if b implies a
        
    b > a
        if a implies b
        

.. method:: ManyRelatedJoinQ.get_prefix_notation(**kwargs)

Classmethods
~~~~~~~~~~~~

.. method:: ManyRelatedJoinQ.from_prefix_notation(exp, **kwargs)

.. method:: ManyRelatedJoinQ.all(*objs)

.. method:: ManyRelatedJoinQ.any(*objs)
    