from django.utils.functional import SimpleLazyObject
from django.core.signals import request_started, request_finished
from django.http import HttpResponseForbidden

from shrubbery.authentication.exceptions import Http403
from shrubbery.authentication.contexts import get_authentication_contexts

class AuthenticationMiddleware(object):
    def process_request(self, request):
        for context in get_authentication_contexts():
            context.user = lambda: context.get_user(request)
    
    def process_response(self, request, response):
        for context in get_authentication_contexts():
            context.user = None
        return response
        
    def process_exception(self, request, exception):
        if isinstance(exception, Http403):
            return HttpResponseForbidden()
        
