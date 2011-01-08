__all__ = []

def export(x):
    __all__.append(x.__name__)
    return x

try:
    any
    all
except NameError:
    @export
    def any(it):
        for x in it:
            if x:
                return True
        return False    

    @export
    def all(it):
        for x in it:
            if not x:
                return False
        return True
        
try:
    min([1], key=lambda x: x)
    max([1], key=lambda x: x)
except TypeError:
    py_min = min
    py_max = max

    @export
    def min(*args, **kwargs):
        key = kwargs.get('key')
        if not key:
            return py_min(*args)
        if len(args) == 1:
            args = args[0]        
        return py_min([(key(arg), arg) for arg in args])[1]
        
    @export
    def max(*args, **kwargs):
        key = kwargs.get('key')
        if not key:
            return py_max(*args)
        if len(args) == 1:
            args = args[0]
        return py_max([(key(arg), arg) for arg in args])[1]
        

        