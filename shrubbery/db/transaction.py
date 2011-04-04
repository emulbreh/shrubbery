from django.db import transaction
from functools import wraps

def wrap_with_savepoint(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            transaction.enter_transaction_management()
            transaction.managed(True)
            sid = transaction.savepoint()
            try:
                res = func(*args, **kwargs)
            except:
                transaction.savepoint_rollback(sid)
                raise
            else:
                transaction.savepoint_commit(sid)
            return res
        finally:
            transaction.leave_transaction_management()
    return decorated

def commit_on_success_unless_managed(func):
    commit_on_success = transaction.commit_on_success(func)
    @wraps(func)
    def decorated(*args, **kwargs):
        if transaction.is_managed():
            try:
                return func(*args, **kwargs)
            finally:
                transaction.set_dirty()
        else:
            return commit_on_success(*args, **kwargs)
    decorated.alters_data = True
    return decorated