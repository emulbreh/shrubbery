from StringIO import StringIO
from django.db import models
from shrubbery.db.utils import get_query_set, force_empty
from shrubbery.utils import reduce_or

def cross_product(*lists):
    result = [[]]
    for seq in lists:
        result = [res + [x] for res in result for x in seq]
    return set(frozenset(res) for res in result)
    
def _add(s, x, set_type):
    if set_type:
        x = set_type((x,))
    return s.union((x,))
    

class ManyRelatedJoinQ(object):
    " Stores a boolean expression of `lookup=obj` terms in conjunctive normal form."
    model = None
    field = None
    lookup = 'exact'
    use_aggregation = True

    def __init__(self, obj=None, lookup=None, model=None):
        self.trivial = None
        if obj:
            self.conjunction = set([frozenset([(obj, False)])])
        else:
            self.conjunction = set()

    def q_for_obj(self, obj, negated=False, lookup=None):
        q = models.Q(**{"%s__%s" % (self.field, lookup or self.lookup): obj})
        if negated:
            q = ~q
        return q        

    def add_to_query(self, query, aliases=None):
        if self.trivial:
            return
        elif self.trivial is False:
            force_empty(query)
        elif self.use_aggregation and len(self.conjunction) > 1 and max(len(disj) for disj in self.conjunction) == 1 and not self.contains_negation():
            conj = [iter(disj).next() for disj in self.conjunction]
            query.add_q(reduce_or(self.q_for_obj(obj, negated) for obj, negated in conj))
            opts = query.model._meta
            if query.group_by is None:
                field_names = [f.attname for f in opts.fields]
                query.add_fields(field_names, False)
                query.set_group_by()
            query.add_aggregate(models.Count(self.field), query.model, 'mrj_count', is_summary=False)
            query.add_q(models.Q(mrj_count=len(conj)))
        else:
            for disj in self.conjunction:
                query.add_q(reduce_or(self.q_for_obj(obj, negated) for obj, negated in disj), set())
            
    def clone(self, conj):
        clone = type(self)()
        clone.conjunction = conj
        clone.optimize()
        return clone
        
    def contains_negation(self):
        for disj in self.conjunction:
            for obj, neg in disj:
                if neg:
                    return True
        return False
        
    @property
    def objects(self):
        return set(obj for obj, neg in disj for disj in self.conjunction)

    @property
    def terms(self):
        return set(reduce(lambda a, b: a.union(b), self.conjunction))
    
    def optimize(self):
        if self.trivial is not None:
            return        
        # First optimize, then negate and optimize two times
        # because _optimize() doesn't get `a & (~a | b) <=> a & b`.
        # - negate: ~(a & (~a | b)) <=> ~a | (a & ~b) <=> (~a | a) & (~a | ~b)
        # - optimize: (~a | a) & (~a | ~b) <=> (~a | ~b)
        # - negate: ~(~a | ~b) <=> a & b
        # - optimize ..        
        conj = self.conjunction
        conj = self._optimize(conj)
        if not conj:
            self.trivial = True
        else:
            conj = self._negate(conj)
            conj = self._optimize(conj)
            if not conj:
                self.trivial = False
            else:
                conj = self._negate(conj)
                conj = self._optimize(conj)
                if not conj:
                    self.trivial = True
        self.conjunction = conj
     
    def _optimize(self, conjunction):
        conj = set(conjunction)
        for disj in conjunction:
            removed = False
            # (a | ~a) <=> True
            for obj, neg in disj:
                if (obj, not neg) in disj:
                    conj.remove(disj)
                    removed = True
                    break
            if not removed:
                # a => (a | b)
                for d in conj:
                    if d < disj:
                        conj.remove(disj)
                        removed = True
                        break
        return conj 
    
    def _negate(self, conjunction):
        # Applying De Morgan's laws we get disjunctive normal form ..
        disj = set(frozenset((obj, not neg) for obj, neg in disj) for disj in conjunction)
        # .. a crossproduct will yield conjunctive normal form again.
        conj = cross_product(*disj)
        return conj        
        
    def __and__(self, other):
        if self.trivial is False:
            return self
        if isinstance(other, self.model):
            conj = _add(self.conjunction, (other, False), frozenset)
            return self.clone(conj)
        elif isinstance(other, type(self)):
            conj = self.conjunction.union(other.conjunction)
            return self.clone(conj)
        raise TypeError()

    def __or__(self, other):
        if self.trivial is True:
            return self
        if isinstance(other, self.model):
            conj = set(_add(disj, (other, False), None) for disj in self.conjunction)
            return self.clone(conj)
        elif isinstance(other, type(self)):
            conj = set(disj.union(other_disj) for disj in self.conjunction for other_disj in other.conjunction)
            return self.clone(conj)
        raise TypeError(type(other))

    def __invert__(self):
        if not self.trivial is None:
            clone = self.clone(set())
            clone.trivial = not self.trivial
            return clone
        else:
            conj = self._negate(self.conjunction)
            return self.clone(conj)

    def __eq__(self, other):
        if self.trivial is not None:
            return self.trivial is other.trivial
        return self.conjunction == other.conjunction
        
    def __ne__(self, other):
        return not(self == other)
        
    def __lt__(self, other):
        if self.trivial is False:
            return True
        elif self.trivial is True:
            return other.trivial is True
        for disj in self.conjunction:
            implied = False
            for other_disj in other.conjunction:
                if disj < other_disj:
                    implied = True
                    break
            if not implied:
                return False
        return True
        
    def __gt__(self, other):
        return other < self        

    def __len__(self):
        return len(self.conjunction)

    def __repr__(self):
        if not self.conjunction:
            return "true"
        sorted_labels = sorted(sorted((unicode(obj), neg) for obj, neg in disj) for disj in self.conjunction)
        return " & ".join([
            "(%s)" % " | ".join([
                "%s%s" % (neg and "~" or "", label) for label, neg in disj
            ]) for disj in sorted_labels
        ])
        
        
    def get_prefix_notation(self, key='pk', and_op='A', or_op='O', not_op='N', separator='-'):
        conj = []
        for disj in self.conjunction:
            ops = or_op * (len(disj) - 1)
            args = separator.join("%s%s" % (neg and not_op or "", getattr(tag, key)) for tag, neg in disj)
            conj.append(ops + args)
        ops = and_op * (len(self.conjunction) - 1)
        args = separator.join(conj)
        return ops + args
    
    @classmethod
    def from_prefix_notation(cls, f, key='pk', and_op='A', or_op='O', not_op='N', separator='-'):
        kwargs = dict(key=key, and_op=and_op, or_op=or_op, not_op=not_op, separator=separator)
        if isinstance(f, (str, unicode)):
            f = StringIO(f)
        c = f.read(1)
        if c == and_op or c == or_op:
            q0 = cls.from_prefix_notation(f, **kwargs)
            comma = f.read(1)
            if comma != separator:
                raise ValueError("'%s' expected" % separator)
            q1 = cls.from_prefix_notation(f, **kwargs)
            if c == and_op:
                return q0 & q1
            elif c == or_op:
                return q0 | q1
        elif c == not_op:
            return ~cls.from_prefix_notation(f, **kwargs)
        else:
            buf = []
            while c and c in "0123456789":
                buf.append(c)            
                c = f.read(1)
            f.seek(f.tell() - 1)
            return get_query_set(cls.model).get(**{key: "".join(buf)}) 

    @classmethod
    def all(cls, *objs):
        return cls().clone(set(frozenset(((obj, False),)) for obj in objs))
        
    @classmethod
    def any(cls, *objs):
        return cls().clone(set([frozenset((obj, False) for obj in objs)]))
    
