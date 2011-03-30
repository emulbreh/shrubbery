import time
import hashlib
import hmac
import base64
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden

from shrubbery.utils.dt import timedelta_seconds


class BadToken(Exception): pass
class TokenExpired(BadToken): pass
class InvalidSignature(BadToken): pass


class SignedTokenFactory(object):
    def __init__(self, secret=settings.SECRET_KEY, hash_length=26):
        self.secret = secret
        self.hash_length = hash_length
    
    def encode(self, data):
        return base64.urlsafe_b64encode(data).rstrip('=')
        
    def decode(self, data):
        return base64.urlsafe_b64decode("%s%s" % (data, '=' * (-len(data) % 4)))
    
    def sign(self, data):
        signature = self.encode(hmac.new(self.secret, data, hashlib.sha1).digest())
        if self.hash_length:
            signature = signature[:self.hash_length]
        return signature
        
    def dumps(self, data):
        data = self.encode(data)
        return "%s%s" % (self.sign(data), data)
        
    def loads(self, data):
        try:
            data = str(data)
        except UnicodeEncodeError:
            raise InvalidSignature("non-ascii data")
        signature, data = data[:self.hash_length], data[self.hash_length:]
        if self.sign(data) != signature:
            raise InvalidSignature
        return self.decode(data)
        

class TimestampedTokenFactory(SignedTokenFactory):
    def __init__(self, ttl=1800, **kwargs):
        super(TimestampedTokenFactory, self).__init__(**kwargs)
        if isinstance(ttl, timedelta):
            ttl = timedelta_seconds(ttl)
        self.ttl = ttl
        
    def dumps(self, data):
        return super(TimestampedTokenFactory, self).dumps("%08x%s" % (int(time.time()), data))
        
    def loads(self, data):
        data = super(TimestampedTokenFactory, self).loads(data)
        try:
            if int(data[:8], 16) + self.ttl < time.time():
                raise TokenExpired
            return data[8:]
        except ValueError:
            raise InvalidSignature("invalid timestamp")
        