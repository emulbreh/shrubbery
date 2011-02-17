from __future__ import with_statement
import threading
from django.utils.functional import wraps
from django.utils.importlib import import_module

from shrubbery.authentication.exceptions import AuthenticationError, Http403
from shrubbery.conf import settings

_authentication_contexts = None

def get_authentication_contexts():
    global _authentication_contexts
    if _authentication_contexts is None:
        _authentication_contexts = []
        for path in settings['shrubbery.authentication'].CONTEXTS:
            module_name, name = path.rsplit('.', 1)
            module = import_module(module_name)
            context = getattr(module, name)
            _authentication_contexts.append(context)
    return _authentication_contexts


class Sudo(object):
    def __init__(self, auth, user):
        self.auth = auth
        self.user = user
        self.base_user = None
        
    def __enter__(self):
        self.base_user = self.auth.user
        self.auth.user = self.user
        
    def __exit__(self, *exc):
        self.auth.user = self.base_user
        
    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorated


_unset = object()


class AuthenticationContext(object):
    def __init__(self, root=None, anonymous=None, session_key=None):
        self.root = root
        self.anonymous = anonymous
        self.stack = threading.local()
        if not session_key:
            session_key = "%s.user-id" % self.__class__.__name__
        self.session_key = session_key
        self.user = self.anonymous
        
    def sudo(self, user=_unset):
        if user is _unset:
            user = self.root
        return Sudo(self, user)
        
    def is_anonymous(self, user):
        return user is self.anonymous
        
    def login(self, request, user):
        self.set_user(request, user)
        
    def logout(self, request):
        self.set_user(request, self.anonymous)
        
    def get_user_id(self, user):
        raise NotImplemented()
        
    def get_user_by_id(self, id):
        raise NotImplemented()
        
    def set_user(self, request, user=_unset):
        if user is not _unset:
            self.user = user
        if self.user:
            request.session[self.session_key] = self.get_user_id(self.user)
        elif self.session_key in request.session:
            del request.session[self.session_key]
        
    def get_user(self, request):
        if self.session_key in request.session:
            try:
                return self.get_user_by_id(request.session[self.session_key])
            except (AuthenticationError, ValueError) as e:
                pass
        return self.anonymous
        
    def _set_user(self, user):
        self.stack.user = user
        
    def _get_user(self):
        if callable(self.stack.user):
            self.stack.user = self.stack.user()
        return self.stack.user
        
    def _del_user(self):
        self.stack.user = self.anonymous
        
    user = property(_get_user, _set_user, _del_user)
        
    def required(self, func=None):
        if not func:
            return self.required
        @wraps(func)
        def _decorated(*args, **kwargs):
            if self.is_anonymous(self.user):
                raise Http403()
            return func(*args, **kwargs)
        return _decorated
        

class ModelAuthenticationContext(AuthenticationContext):
    def __init__(self, **kwargs):
        if 'queryset' in kwargs:
            self.queryset = kwargs.pop('queryset')
        super(ModelAuthenticationContext, self).__init__(**kwargs)
        
    def get_user_id(self, user):
        return user.pk
        
    def get_user_by_id(self, user_id):
        try:
            return self.queryset.get(pk=user_id)
        except self.queryset.model.DoesNotExist:
            raise ValueError("invalid user id: %s" % user_id)
