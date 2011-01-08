import inspect

from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

class Setting(object):
    def __init__(self, validators=None, legacy_setting=None, help=None, resolve_callable=False, **kwargs):
        self.legacy_setting = legacy_setting
        self.help = help
        self.resolve_callable = resolve_callable
        self.validators = validators or () 
        if 'default' in kwargs:
            self.default = kwargs['default']

    def normalize(self, value):
        if self.resolve_callable:
            value = value()
        return value
        
    def __get__(self, instance, cls=None):
        if instance is None:
            instance = cls.instance
        try:
            value, raw = instance[self.name]
        except KeyError:
            from django.conf import settings as global_settings
            if self.legacy_setting and hasattr(global_settings, self.legacy_setting):
                value, raw = getattr(global_settings, self.legacy_setting), True
            elif hasattr(self, 'default'):
                value, raw = self.default, True
            else:
                instance.missing_setting(self)
        if raw:
            value = self.normalize(value)
            instance[self.name] = value, False
        return value
    
    def __set__(self, instance, value):
        instance[self.name] = value, True

    def __delete__(self, instance):
        del instance[self.name]

class Registry(object):
    def __init__(self):
        self._registry = {}
        self._module_to_app = {}
        
    def __getitem__(self, module_name):
        if module_name not in self._registry:
            self._registry[module_name] = import_module("%s.conf" % module_name).settings                
        return self._registry[module_name]
        
    def __getattr__(self, name):
        from django.conf import settings as global_settings
        return getattr(global_settings, name)
        
    def local(self):
        name = inspect.currentframe().f_back.f_globals['__name__']
        if name in self._module_to_app:
            calling_app = self._module_to_app[name]
        else:
            calling_app = None
            for app in self.INSTALLED_APPS:
                if name.startswith("%s." % app):
                    calling_app = app
                    break
            assert calling_app is not None, "shrubbery.conf.settings.local() must be called from an installed app, called from: %s" % name
            self._module_to_app[name] = calling_app
        return self[calling_app]
        
settings = Registry()

app_settings = {}

class SettingsBase(type):
    def __new__(cls, name, bases, attribs):     
        settings_cls = type.__new__(cls, name, bases, attribs)
        s = {}
        for name, value in attribs.items():
            if isinstance(value, Setting):
                s[name] = value
                value.name = name
        settings_cls._settings = s
        settings._registry[settings_cls.__module__] = settings_cls      
        return settings_cls
    
    @property
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
            app_config = app_settings.get(cls._instance.app_module, {})
            cls.configure(app_config)
        return cls._instance
            
    def configure(cls, config):
        cls.instance.load(config)
        
class Settings(object):
    __metaclass__ = SettingsBase
    def __init__(self, config=None):
        self._values = {}
        if config:
            self.load(config)
        
    def __iter__(self):
        return iter(self._settings)
        
    def __getitem__(self, name):
        return self._values[name]
        
    def __setitem__(self, name, value):
        self._values[name] = value
        
    def __delitem__(self, name):
        del self._values[name]
    
    def as_dict(self):
        d = {}
        for name in self:
            d[name] = getattr(self, name)
        return d
    
    def load(self, config):
        if callable(config):
            config = config()
        if isinstance(config, dict):
            for name in self:
                if name in config:
                    setattr(self, name, config[name])
        else:
            if isinstance(config, str):
                try:
                    config = import_module(config)
                except ImportError:
                    module, name = config.rsplit('.', 1)
                    config = getattr(import_module(module), name)
                    return self.load(config)
            for name in self:
                if hasattr(config, name):
                    setattr(self, name, getattr(config, name))

    def validate(self):
        for name, setting in self._settings.items():
            try:
                setting.validate(self, getattr(self, name))
            except ValueError, e:
                raise ImpropertyConfigured("invalid setting %s for app '%s': %s" \
                    % (setting.name, self.app_label, e))
            
    @property
    def app_module(self):
        return self.__module__.rsplit('.', 1)[0]

    @property
    def app_label(self):
        return self.__module__.rsplit('.', 2)[-2]
            
    def missing_setting(self, setting):
        raise ImproperlyConfigured("missing setting %s for app '%s': %s" \
            % (setting.name, self.app_label, setting.help or 'required'))
