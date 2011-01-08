from django.db import connection, models

def replace_references(to_obj, with_obj):
    model = to_obj.__class__
    assert isinstance(with_obj, model)
    for rel_obj, related_model in model._meta.get_all_related_objects_with_model():
        rel_field = rel_obj.field
        accessor = rel_obj.get_accessor_name()
        rel_manager = getattr(to_obj, accessor)
        
        if isinstance(rel_field, models.ManyToManyField):
            qn = connection.ops.quote_name            
            sql = """UPDATE %s SET %s = %%s WHERE %s = %%s""" % (
                qn(rel_field.m2m_db_table),
                qn(rel_field.m2m_reverse_name),
                qn(rel_field.m2m_column_name),
            )
            cursor = connection.cursor()
            cursor.execute(sql, (with_obj.pk, to_obj.pk))
        else:
            rel_manager.update(**{rel_field.name: with_obj})

def replace(obj, with_obj):
    replace_references(obj, with_obj)
    obj.delete()
