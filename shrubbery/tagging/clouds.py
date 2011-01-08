import math
from django.db import models
from shrubbery.db.utils import get_query_set
from shrubbery.db.union import UnionQuerySet
from shrubbery.tagging.models import Tagged

def LINEAR(count, min_count, max_count, avg_count):
    return count / float(max_count)

def LOGARITHMIC(count, min_count, max_count, avg_count):
    if max_count == 1:
        return 1
    return math.log(count) / math.log(max_count)

def COUNT(count, min_count, max_count, avg_count):
    return int(count)

class Annotation(object):
    def __init__(self, distribution=None, steps=None):
        self.distribute = distribution
        if isinstance(steps, int):
            steps = range(steps)
        self.steps = steps

    def __call__(self, tag, count, min_count, max_count, avg_count):
        value = self.distribute(count, min_count, max_count, avg_count)
        if self.steps:
            if value == 1:
                return self.steps[-1]
            value = self.steps[int(value * len(self.steps))]
        return value

    @classmethod
    def LINEAR(cls, **kwargs):
        kwargs['distribution'] = LINEAR
        return cls(**kwargs)

    @classmethod
    def LOGARITHMIC(cls, **kwargs):
        kwargs['distribution'] = LOGARITHMIC
        return cls(**kwargs)
    
    @classmethod
    def COUNT(cls, **kwargs):
        kwargs['distribution'] = COUNT
        return cls(**kwargs)

    

DEFAULT_ANNOTATIONS = {}

class Cloud(object):    
    def __init__(self, queryset=None, tags=None, **kwargs):
        self.union = isinstance(queryset, UnionQuerySet)
        self.threshold = kwargs.pop('threshold', 0)
        self.annotations = kwargs.pop('annotations', DEFAULT_ANNOTATIONS)
        self.range_adjusted = kwargs.pop('range_adjusted', True)
        if queryset:
            if not self.union:
                queryset = get_query_set(queryset)            
            if tags:
                tags = tags & queryset.tags()
            else:
                tags = queryset.tags()
            self.queryset = queryset
        else:
            self.queryset = UnionQuerySet(Tagged)
            self.union = True
        self.tags = tags.annotate(_count=models.Count('object_set')).order_by('-_count')
        if self.threshold:
            self.tags = self.tags.filter(_count__gte=self.threshold)
        
    @property
    def cache_key(self):
        from hashlib import sha1
        return "cloud_%s" % sha1("%s;%s" % (str(self.tags.query), repr(self.annotations))).hexdigest()

    def clone(self, tags=None):
        clone = object()
        clone.__class__ = type(self)
        clone.tags = tags or self.tags
        clone.annotations = self.annotations
        clone.range_adjusted = clone.range_adjusted
        return clone
        
    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.clone(tags=self.tags[key])
        else:
            return self.tags[key]
            
    @property
    def coverage(self):
        return self.queryset.coverage(self.tags)
    
    @property
    def cloud(self):
        if not hasattr(self, '_cloud'):
            tags = list(self.tags)
            if not tags:
                max_count = 1
            else:
                min_count = float(tags[-1]._count)
                max_count = float(tags[0]._count)
                avg_count = float(sum(tag._count for tag in tags)) / len(tags)
                tags.sort(key=lambda tag: tag.name)
                if self.range_adjusted:
                    max_count = max_count - min_count + 1
                for tag in tags:
                    count = tag._count
                    if self.range_adjusted:
                        count = count - min_count + 1
                    for attr, annotation in self.annotations.items():
                        setattr(tag, attr, annotation(tag, count, min_count, max_count, avg_count))        
            self._cloud = tags
            self.max_count = max_count
        return self._cloud
        
    def __iter__(self):
        return iter(self.cloud)
        
    def kmeans(self, k, point=lambda t: t.count, metric=lambda a,b: abs(a-b)):
        tags = self.cloud
        means = [1 + (self.max_count-1)*float(i)/k for i in range(k)]
        prev_clusters = None
        while True:
            clusters = [set() for i in range(k)]
            for tag in tags:
                p = point(tag)
                index, mean = min(enumerate(means), key=lambda x: metric(x[1], p))
                clusters[index].add(tag)
            for index, cluster in enumerate(clusters):
                if not cluster:
                    tag = max(clusters, key=lambda c: len(c)).pop()
                    cluster.add(tag)
                means[index] = float(sum(point(tag) for tag in cluster)) / len(cluster)
            if clusters == prev_clusters:
                break
            prev_clusters = clusters[:]
        return clusters
            
    def __repr__(self):
        tags = [] 
        for tag in self:
            a = []
            for attr in self.annotations:
                a.append("%s: %s" % (attr, getattr(tag, attr)))
            tags.append("%s: {%s}" % (tag.name, ", ".join(a)))
        return ", ".join(tags)
