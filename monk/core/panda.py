# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
from ..math.cmath import sigmoid
import constants as cons
import base, crane
import re
import logging
logger = logging.getLogger('monk.panda')

class Panda(base.MONKObject):
    FUID  = 'uid'
    FNAME = 'name'
    store = crane.pandaStore
    
    def __default__(self):
        super(Panda, self).__default__()
        self.uid = crane.uidStore.nextUID()
        self.name = 'Var' + str(self.uid)
        
    def has_mantis():
        return False
    
    def add_features(self, uids):
        pass
    
    def train(self):
        pass
    
    def predict(self, entity):
        return 0

class ImmutablePanda(Panda):
    '''
    These pandas won't be replicated for different users
    '''
    def __default__(self):
        super(ImmutablePanda, self).__default__()
        self.creator = cons.DEFAULT_CREATOR
    
    def __restore__(self):
        super(ImmutablePanda, self).__restore__()
        self.creator = cons.DEFAULT_CREATOR
    
    def clone(self, user):
        return self
        
class ExistPanda(ImmutablePanda):

    def predict(self, entity):
        if self.name in entity._raws:
            entity[self.uid] = 1
            return 1
        else:
            return 0

class RegexPanda(ImmutablePanda):

    def __restore__(self):
        super(RegexPanda, self).__restore__()
        self.p = re.compile(self.name)
    
    def generic(self):
        result = super(RegexPanda, self).generic()
        del result['p']
        return result
        
    def predict(self, entity):
        if [v for k,v in entity._raws.iteritems() if self.p.match(k)]:
            entity[self.uid] = 1
            return 1
        else:
            return 0

class LinearPanda(Panda):
    FWEIGHTS = 'weights'
    FMANTIS  = 'mantis'

    def __default__(self):
        super(LinearPanda, self).__default__()
        self.weights = FlexibleVector()
        self.mantis = None

    def __restore__(self):
        super(LinearPanda, self).__restore__()
        self.weights = FlexibleVector(generic=self.weights)
        if isinstance(self.mantis, dict):
            self.mantis['panda'] = self._id
        self.mantis = crane.mantisStore.load_or_create(self.mantis)

    def generic(self):
        result = super(LinearPanda, self).generic()
        result[self.FMANTIS]  = self.mantis.name
        result[self.FWEIGHTS] = self.weights.generic()
        return result
    
    def clone(self, user):
        obj = super(LinearPanda, self).clone(user)
        obj.weights = self.weights.clone()
        obj.mantis = self.mantis.clone(user)
        return obj
        
    def save(self, **kwargs):
        super(LinearPanda, self).save(kwargs)
        self.mantis.save(kwargs)
    
    def delete(self):
        result = super(LinearPanda, self).delete()
        result = result & self.mantis.delete()
        return result
        
    def has_mantis(self):
        return True
    
    def add_features(self, uids):
        self.weights.addKeys(uids)
    
    def pull_weights(self):
        genericW = self.store.load_one_in_fields(self, [self.FWEIGHTS])
        self.weights.update(genericW.get(self.FWEIGHTS, []))
    
    def push_weights(self):
        self.store.update_one_in_fields(self, {self.FWEIGHTS:self.weights.generic()})
        
    def predict(self, entity):
        entity[self.uid] = sigmoid(self.weights.dot(entity._features))
        return entity[self.uid]

base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)
