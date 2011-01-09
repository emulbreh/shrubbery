.. include:: ../_lib/links.rst

=================
Why not use … ?
=================
 
.. _why_not_django_tagging:

Why not django-tagging?
=======================

`django-tagging`_ is fine for most use cases. 
But as a consequence of using raw SQL and limitations of `django.contrib.contenttypes`_, it doesn't allow you to use intuitive django query syntax (let ``foo_qs`` be a queryset of tagged objects):

.. code-block:: python

    foo_qs.filter(tags=tag)
    # in django-tagging:
    TaggedItem.objects.get_by_model(foo_qs, tag)
    
    foo_qs.filter(tags=tag_1).filter(tags=tag_2)
    # in django-tagging:
    TaggedItem.objects.get_intersection_by_model(foo_qs, [tag_1, tag_2])
    # the django-tagging solution uses a separate query, but won't require a join per tag. 
    # The following is closer:
    foo_qs.filter(tags__in=[tag_1, tag_2]).annotate(count=Count('tags')).filter(count=2)
    
    foo_qs.filter(tags__in=[tag_1, tag_2])
    # in django-tagging:
    TaggedItem.objects.get_union_by_model(foo_qs, [tag_1, tag_2])
        
    Tag.objects.filter(object_set__in=foo_qs.values('pk').query).annotate(count=Count('object_set')).filter(count__gte=5)
    # in django-tagging (shorter, but returns a list instead of a QuerySet):
    Tag.objects.usage_for_queryset(foo_qs, counts=True, min_count=5)
    # in shrubbery.tagging:
    foo_qs.tags().annotate(count=Count('object_set')).filter(count__gte=5)
    
    foo_qs.exclude(tags=tag)
    # workaround with django-tagging:
    foo_qs.exclude(pk__in=TaggedItem.objects.get_by_model(foo_qs.values('pk').query)

.. note:: When I wrote this, `django-taggit`_ didn't exist. While it has a much nicer API for querying the tagged objects it still suffers from its contenttypes dependency: it cannot support aggregates.


.. _why_not_contenttypes:

Why not contenttypes?
=====================

Reasons not to use `django.contrib.contenttypes`_:

 * ``GenericForeignKey`` does not support the `QuerySet`_ lookup API.
 * No builtin many-to-many relations.
 * ``GenericForeignKey`` requires three fields on your model. If you use non-default names, you'll write two of them twice. 
 * ``GenericRelation`` does not support aggregates.


