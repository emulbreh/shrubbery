from django.utils.importlib import import_module

from shrubbery.conf.base import Setting, Settings, settings

class IntSetting(Setting):
    pass

class BooleanSetting(Setting):
    pass
    
class ImportSetting(Setting):
    def __init__(self, **kwargs):
        self.resolve_callable = kwargs.pop('resolve_callable', False)
        super(ImportSetting, self).__init__(kwargs)
            
    def normalize(self, value):
        if isinstance(value, str):
            module, name = value.rsplit('.', 1)
            value = getattr(import_module(module), name)
        return super(ImportSetting, self).normalize(value)
        
class ModuleSetting(Setting):
    def normalize(self, value):
        if isinstance(value, str):
            return import_module(value)
        return super(ModuleSetting, self).normalize(value)

