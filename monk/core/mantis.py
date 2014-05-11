# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from ..math.svm_solver_dual import SVMDual
from ..math.flexible_vector import FlexibleVector
from bson.objectid import ObjectId
import logging
logger = logging.getLogger("monk.mantis")

class Mantis(base.MONKObject):
    FEPS = 'eps'
    FLAM = 'lam'
    FRHO = 'rho'
    FPANDA = 'panda'
    FDATA = 'data'
    FSOLVER = 'solver'
    FZ = 'z'
    FMAX_NUM_ITERS = 'maxNumIters'
    FMAX_NUM_INSTANCES = 'maxNumInstances'
    store = crane.mantisStore
    
    def __default__(self):
        self.eps = 1e-4
        self.lam = 1
        self.rho = 1
        self.maxNumIters = 1000
        self.maxNumInstances = 1000
        self.panda = None
        self.data = {}
        
    def __restore__(self):
        super(Mantis, self).__restore__()
        self.panda = crane.pandaStore.load_one_by_id(self.panda)
        self.solver = None
        self.z = FlexibleVector()
        try:
                w = self.panda.weights
                self.solver = SVMDual(w, self.eps, self.lam,
                                      self.rho, self.maxNumIters,
                                      self.maxNumInstances)
        except Exception as e:
            logger.error('can not create a solver for {0}'.format(self.panda.name))
            logger.error('error {0}'.format(e.message))
            return False

    def generic(self):
        result = super(Mantis, self).generic()
        # every mantis should have a panda
        result[self.FPANDA] = self.panda._id
        try:
            del result[self.FSOLVER]
            del result[self.FZ]
        except Exception as e:
            logger.warning('deleting solver failed {0}'.format(e.message))
        return result
    
    def sync_consensus(self, leader):
        self.z.update(self.solver.update(crane.pandaStore.load_one(
                                         {'name':self.panda.name,
                                          'creator':leader},
                                         {'weights':True})))
        if self.solver:
            self.solver.setModel(self.z)
                                                     
        
    def train(self, leader):
        if self.solver:
            self.solver.trainModel()
    
    def add_data(self, entity, y, c):
        if self.solver:
            da = self.data
            uuid = entity._id
            if uuid in da:
                ind = da[uuid][0]
            elif self.solver.num_instances < self.maxNumInstances:
                ind = self.solver.num_instances
                self.solver.num_instances = ind + 1
            else:
                # random replacement policy
                # TODO: should replace the most confident data
                olduuid, (ind, oldy, oldc)  = da.popitem()
            self.solver.setData(entity._features, y, c, ind)
            da[uuid] = (ind, y, c)
    
    def merge(self, user):
        # TODO: incremental aggregation
        # TODO: ADMM aggregation
        consensus = self.panda.weights
        t = len(self.panda.weights)
        if userId in self.panda.weights:
            w = self.panda.weights[userId]
        else:
            w = consensus
            t += 1
        consensus.add(w, -1/t)
        self.panda.load_one_weight(userId)
        if userId in self.panda.weights:
            w = self.panda.weights[userId]
        else:
            w = consensus
        consensus.add(w, 1/t)
        self.panda.save_consensus()
    
    def has_user(self, userId):
        return userId in self.data
    
    def has_user_in_store(self, userId):
        field = 'data.{0}'.format(userId)
        return crane.mantisStore.exists_field(self, field)
        
    def add_one(self, userId):
        if not self.has_user_in_store(userId):
            try:
                w = self.panda.get_model(userId)
                self.solvers[userId] = SVMDual(w, self.eps, self.lam,
                                                     self.rho, self.maxNumIters,
                                                     self.maxNumInstances)
                self.data[userId] = {}
                fields = {'data.{0}'.format(userId):{}}
                return crane.mantisStore.update_one_in_fields(self, fields)
            except Exception as e:
                logger.error('can not create a solver for {0}'.format(userId))
                logger.error('error {0}'.format(e.message))
                return False
        else:
            logger.error('mantis {0} already stores user {1}'.format(self._id, userId))
            return False
    
    def remove_one(self, userId):
        if self.has_user_in_store(userId):
            field = 'data.{0}'.format(userId)
            result = crane.mantisStore.remove_field(self, field)
            if userId in self.solvers:
                del self.solvers[userId]
            if userId in self.data:
                del self.data[userId]
            return result
        else:
            logger.warning('mantis {0} does not store user {1}'.format(self._id, userId))
            return False            
        
    def load_one(self, userId):
        if self.has_user_in_store(userId):
            fields = ['data.{0}'.format(userId)]
            s = crane.mantisStore.load_one_in_fields(self, fields)
            w = self.panda.get_model(userId)
            solver = SVMDual(w, self.eps, self.lam,
                             self.rho, self.maxNumIters,
                             self.maxNumInstances)
            self.solvers[userId] = solver
    
            #@todo: slow, need to optimize
            da = s['data'][userId]
            da = {ObjectId(k) : v for k,v in da.iteritems()}
            self.data[userId] = da
            ents = crane.entityStore.load_all_by_ids(da.keys())
            for ent in ents:
                index, y, c = da[ent._id]
                solver.setData(ent._features, y, c, index)
            return True
        else:
            logger.warning('mantis {0} does not store user {1}'.format(self._id, userId))
            return False            
    
    def unload_one(self, userId):
        if self.has_user(userId):
            fields = {'data.{0}'.format(userId):{str(k):v for k,v in self.data[userId].iteritems()}}
            result = crane.mantisStore.update_one_in_fields(self, fields)
            del self.solvers[userId]
            del self.data[userId]
            return result
        else:
            logger.warning('mantis {0} does not have user {1}'.format(self._id, userId))
            return False
            
    def save_one(self, userId):
        if self.has_user(userId):
            fields = {'data.{0}'.format(userId):{str(k):v for k,v in self.data[userId].iteritems()}}
            return crane.mantisStore.update_one_in_fields(self, fields)
        else:
            logger.warning('mantis {0} does not have user {1}'.format(self._id, userId))
            return False
            
base.register(Mantis)
