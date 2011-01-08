from django.db.models.base import Model, ModelBase

class VirtualModelBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        model = super(VirtualModelBase, cls).__new__(cls, name, bases, attrs)
        if name != 'VirtualModel':
            model._meta.virtual = VirtualModel in bases
        return model
        
class VirtualModel(Model):
    __metaclass__ = VirtualModelBase
    class Meta:
        abstract = True
        
    def save(self, force_insert=False, force_update=False):
        cls = self.__class__
        if cls._meta.virtual and not force_update:            
            pk = self.pk
            if force_insert or not pk or not cls._base_manager.filter(pk=pk).extra(select={'a': 1}).values('a').order_by(): 
                raise AttributeError("Virtual model instances cannot be created directly.")
            force_update = True
        return super(VirtualModel, self).save(force_insert=force_insert, force_update=force_update)

