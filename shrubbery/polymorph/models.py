from django.db import models, transaction
from django.utils.importlib import import_module

from shrubbery.conf import settings
from shrubbery.db.managers import Manager
from shrubbery.db.utils import get_sub_models, get_query_set, get_model, remove_join, forge_join
from shrubbery.db.union import UnionQuerySet
from shrubbery.db import extensions as ext

polymorph_settings = settings['shrubbery.polymorph']

### querysets and managers ###

class ObjectIdentityQuerySet(models.query.QuerySet):
    @Manager.proxy_method
    def coerce(self, model, subquery=False):
        if self.model != ObjectIdentity:
            raise AttributeError("coerce() is only available for abstract models")
        qs = get_query_set(model)
        if subquery:
            return qs.filter(id__in=self.filter(type=Type.objects.get_for_model(model)).values('pk').query)
        clone = self._clone(klass=type(qs)) 
        query = clone.query
        query.clear_select_fields()
        #query.remove_inherited_models()

        obj_alias = query.get_initial_alias()
        obj_table = query.alias_map[obj_alias][0]            
        table = model._meta.db_table
        alias, _ = query.table_alias(table, True)
        identity_col = Object._meta.get_field('id').db_column
        
        remove_join(query, obj_alias)            
        forge_join(query, table, alias, None, None, None, None)            
        forge_join(query, obj_table, obj_alias, table, alias, identity_col, 'id')            
        query.tables.insert(0, query.tables.pop())            
        query.model = model
        
        # replace ObjectIdentity.pk-joins with model.pk-joins
        for rhs_alias, join in query.alias_map.items():
            rhs_table, rhs_alias, join_type, lhs_alias, lhs_col, rhs_col, nullable = join
            if lhs_alias == obj_alias and lhs_col == 'id':
                remove_join(query, rhs_alias)
                forge_join(query, rhs_table, rhs_alias, table, alias, identity_col, rhs_col, join_type=join_type, nullable=nullable)
                query.unref_alias(obj_alias)
         
        # if `obj_alias` is referenced only once, then it's our forged inner join with `table`. it can be removed.
        if query.alias_refcount[obj_alias] == 1:
            remove_join(query, obj_alias, True)
        
        clone.model = model        
        return clone            

    @Manager.proxy_method
    def types(self):
        return Type.objects.filter(pk__in=self.values('type_id').query).distinct()
        
    @Manager.proxy_method
    def models(self):
        return [t.model for t in self.types()]

    @Manager.proxy_method
    def instances(self, *models):
        if self.model != ObjectIdentity:
            raise AttributeError("instances() is only available on abstract models")        
        if not models:
            models = self.models()
        return UnionQuerySet(*[self.coerce(submodel) for submodel in models])    


class ObjectIdentityManager(Manager):
    def __init__(self, for_model=None):        
        super(ObjectIdentityManager, self).__init__()
        if for_model:
            self.model = ObjectIdentity
            self.for_model = for_model
        else:
            self.for_model = None
        
    def get_query_set(self):
        qs = super(ObjectIdentityManager, self).get_query_set()
        if self.for_model:
            qs = qs.filter(type=Type.objects.get_for_model(self.for_model))
        return qs

    class Meta:
        queryset = ObjectIdentityQuerySet
        
class ObjectIdentitiesDescriptor(object):
    def __get__(self, instance, model=None):
        if instance:
            raise AttributeError('Object.indentities is only accessible on models, not on Object instances.')
        return ObjectIdentityManager(for_model=model)
        
class ObjectQuerySet(models.query.QuerySet):
    @Manager.proxy_method
    def identities(self):
        return ObjectIdentity.objects.filter(pk__in=self.values('pk').query)

class ObjectManager(ObjectIdentityManager):
    def get_query_set(self):
        if self.model._meta.abstract:
            models = get_sub_models(self.model, abstract=False, direct=True)
            return ObjectIdentity.objects.filter(type__in=[Type.objects.get_for_model(model) for model in models])
        else:
            return super(ObjectManager, self).get_query_set()
            

class TypeManager(ObjectManager):
    _model_cache = {}
    _pk_cache = {}
    
    def get_by_pk(self, pk):
        cache = self.__class__._pk_cache
        if pk not in cache:
            t = Type.objects.get(pk=pk)
            cache[pk] = t
            self.__class__._model_cache[t.model] = t
        return cache[pk]
        
    def get_by_natural_key(self, module_name, name):
        return self.get(name=name, module_name=module_name)

    def get_for_model(self, model):
        model = get_model(model, proxy=False)
        cache = self.__class__._model_cache
        if model not in cache:
            name = model.__name__
            module_name = model.__module__
            try:
                t = self.get(name=name, module_name=module_name)
            except Type.DoesNotExist:
                if model == Type:
                    transaction.enter_transaction_management()
                    identity = ObjectIdentity.objects.create(type_id=0)
                    t = Type.objects.create(id=identity, name=name, module_name=module_name, abstract=model._meta.abstract)
                    identity.type = t
                    identity.save()
                    transaction.commit()
                    transaction.leave_transaction_management()
                else:
                    t = Type.objects.create(module_name=module_name, name=name, abstract=model._meta.abstract)
            #cache[model] = t
            #self.__class__._model_cache[t.pk] = t
            return t
        return cache[model]
    
    def get_for_instance(self, obj):
        return self.get_for_model(type(obj))
        
    def clear_cache(self):
        self.__class__._model_cache = {}
        self.__class__._pk_cache = {}

class TypeField(ext.ForeignKey):
    def __init__(self, **kwargs):
        kwargs['to'] = 'polymorph.Type'
        super(TypeField, self).__init__(**kwargs)

    def get_prep_lookup(self, lookup, val):
        if lookup == 'in':
            val = [isinstance(obj, models.base.ModelBase) and Type.objects.get_for_model(obj) or obj for obj in val]
        return super(TypeField, self).get_prep_lookup(lookup, val)


### models ###
class ObjectIdentity(models.Model):
    # prevent subclasses from messing with our PK:
    id = models.AutoField(primary_key=True)
    type = TypeField()

    objects = ObjectIdentityManager()
    
    class Meta:
        db_table = polymorph_settings.OBJECT_IDENTITY_DB_TABLE

    def coerce(self, model):
        if isinstance(model, Type):
            model = model.model
        return getattr(self, "%s_%s_instance" % (model._meta.app_label, model.__name__.lower()))
    
    def __unicode__(self):
        return u"%s, type=%s" % (self.id, self.type_id)

    def __int__(self):
        return self.pk

    @property
    def instance(self):
        return self.coerce(self.type)


class Object(models.Model):
    id = ext.OneToOneField(ObjectIdentity, primary_key=True, related_name='%(app_label)s_%(class)s_instance', db_column=polymorph_settings.OBJECT_IDENTITY_DB_COLUMN)    

    objects = ObjectManager()
    identities = ObjectIdentitiesDescriptor()
    
    class Meta:
        abstract = True

    def save(self, **kwargs):
        if not self.pk:
            self.id = ObjectIdentity.objects.create(type=Type.objects.get_for_instance(self))
        return super(Object, self).save(**kwargs)


class Type(Object):
    module_name = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    abstract = models.BooleanField(default=False)
    
    objects = TypeManager()
    
    class Meta:
        unique_together = ('module_name', 'name')
        
    def __unicode__(self):
        return "%s@%s, abstract=%s" % (self.name, self.module_name, self.abstract)
        
    def natural_key(self):
        return (self.module_name, self.name)

    @property
    def model(self):
        return getattr(self.module, self.name)

    @property
    def module(self):
        return import_module(self.module_name)

    @property
    def app_label(self):
        return self.model._meta.app_label

    if 'django.contrib.contenttypes' in settings.INSTALLED_APPS:
        @property
        def content_type(self):
            from django.contrib.contenttypes.models import ContentType
            return ContentType.objects.get_for_model(self.model)


def _post_init(sender, **kwargs):
    obj = kwargs['instance']
    #if isinstance(obj, Object) and obj.pk and not hasattr(obj, '_id_cache') and not isinstance(obj, Type):
    #    obj._id_cache = ObjectIdentity(id=obj.pk, type=Type.objects.get_for_instance(obj))
    #if isinstance(obj, ObjectIdentity) and obj.type_id and not hasattr(obj, '_type_cache'):
    #    obj.type = Type.objects.get_by_pk(obj.type_id)
models.signals.post_init.connect(_post_init)

def _post_delete(sender, **kwargs):
    instance = kwargs['instance']
    if isinstance(instance, Object):
        try:
            instance.id.delete()
        except ObjectIdentity.DoesNotExist:
            pass
models.signals.post_delete.connect(_post_delete)


if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^shrubbery\.polymorph\.models\.TypeField$'])
