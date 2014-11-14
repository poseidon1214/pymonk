# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 00:16:27 2014

@author: xm
"""

import base
import crane
import entity
import datetime
from constants import DEFAULT_NONE, DEFAULT_EMPTY
import logging

logger = logging.getLogger("monk.engine")

class Engine(entity.Entity):
    FADDRESS    = 'address'
    FPID        = 'pid'
    FPARTITION  = 'partition'
    FSTATUS     = 'status'
    FUSERS      = 'users'
    FSTARTTIME  = 'starttime'
    FENDTIME    = 'endtime'
    
    store = crane.engineStore
    
    def __default__(self):
        super(Engine, self).__default__()
        self.address = DEFAULT_EMPTY
        self.pid = DEFAULT_EMPTY
        self.partitions = []
        self.status = 'inactive'
        self.starttime = datetime.datetime.now()
        self.endtime = datetime.datetime.now()
        self.users = []
        
    def __restore__(self):
        super(Engine, self).__restore__()
        
    def generic(self):
        result = super(Engine, self).generic()
        result[self.FSTARTTIME] = self.starttime.isoformat()
        result[self.FENDTIME] = self.endtime.isoformat()
        return result

    def clone(self, userName):
        ''' Engine can not be replicated '''
        return None
    
    def addUser(self, userName):
        self.users.append(userName)
        self.store.push_one_in_fields(self, {'users':userName})
        
base.register(Engine)