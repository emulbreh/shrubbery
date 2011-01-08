from django.db import models
from shrubbery.db.transaction import commit_on_success_unless_managed

def create_manager(superclass, key_attr, value_attr):
    
    class ReverseManagerMixin(superclass):
        def _create_item(self, key, value):
            return self.create(**{key_attr: key, value_attr: value})
            
        def _update_item(self, key, value):
            return self.filter(**{key_attr: key}).update(**{value_attr: value})

        def _get_item(self, key):
            return self.get(**{key_attr: key})
