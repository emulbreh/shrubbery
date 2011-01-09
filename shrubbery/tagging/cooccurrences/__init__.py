import math
from shrubbery.db.utils import get_query_set
from shrubbery.tagging.models import Tag

def _count(q, queryset=None):
    if queryset:
        queryset = get_query_set(queryset)
        if q:
            queryset = queryset.complex_filter(q)
        return float(queryset.count())
    else:
        return Tag.objects.object_set().filter(TagQ(q, field='object_set__tags'))

def jaccard(a, b, queryset=None):
    return _count(a & b, queryset) / _count(a | b, queryset)
    
def cossim(a, b, queryset=None):
    "cossim(a, b) = arccos(v_a, v_b) = (v_a * v_b)/(|v_a|*|v_b|) for v_x[t] = w(x, t)"
    queryset = get_query_set(queryset)
    p, n_a, n_b = 0, 0, 0
    for t in queryset.complex_filter(a & b).tags():
        if a == t or b == t:
            continue
        v_at = _count(a & t, queryset)
        v_bt = _count(b & t, queryset)
        p += v_at * v_bt
        n_a += v_at ** 2
        n_b += v_bt ** 2
    if p == 0:
        return 0
    return p / (math.sqrt(n_a) * math.sqrt(n_b))
    
def dijunct(a, b, queryset=None):
    return _count(a & b) == 0
    
def probability(a, given=None, queryset=None):
    if not given:
        return _count(a, queryset) / _count(None, queryset)
    else:
        return _count(a & given, queryset) / _count(given, queryset)

def implies(a, b, queryset=None):
    return probability(b, given=a, queryset=queryset) == 1

