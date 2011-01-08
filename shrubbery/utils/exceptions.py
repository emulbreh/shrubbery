import sys, traceback
from StringIO import StringIO

class ChainableException(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = sys.exc_info()
        super(ChainableException, self).__init__(*args, **kwargs)
        
    def __str__(self):
        s = super(ChainableException, self).__str__()
        if self.cause:
            s += " [Caused by:\n\t"
            cause_tb = StringIO()
            traceback.print_exception(*(self.cause + (None, cause_tb)))
            s += cause_tb.getvalue().replace("\n", "\n\t") + "]"
        return s