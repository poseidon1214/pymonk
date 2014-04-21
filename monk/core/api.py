# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
import logging.config
from bson.objectid import ObjectId
# to register classes in base
import base, crane, entity, relation, tigress, turtle, mantis, panda
import configuration
import yaml
from constants import *

logger = logging.getLogger("monk.api")
_config = None

# utility APIs
def UUID(objId=None):
    if objId is None:
        return ObjectId()
    elif isinstance(objId, basestring):
        return ObjectId(objId)
    else:
        return objId

def yaml2json(yamlFileName):
    with open(yamlFileName, 'r') as yf:
        return yaml.load(yf)
    return None
    
def initialize(config=None):
    global _config
    if config is not None:
        if isinstance(config, basestring):
            _config = configuration.Configuration(config)
        else:
            _config = config
    
    logging.config.dictConfig(_config.loggingConfig)
    logger.info('------start up------')
    return crane.initialize_storage(_config)

def exits():
    logger.info('------end-----------')
    crane.exit_storage()
    return True

def reloads():
    global _config
    if _config is None:
        return
    exits()
    reload(base)
    reload(crane)
    reload(entity)
    reload(relation)
    reload(tigress)
    reload(turtle)
    reload(mantis)
    reload(panda)
    initialize()
    
# entity APIs
def get_entities(query=None, fields=None, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    return crane.entityStore.load_all(query, fields)

def load_entities(entities, collectionName=None):
    if not entities:
        crane.entityStore.set_collection_name(collectionName)
        entities = [ent['_id'] for ent in crane.entityStore.load_all_in_ids({})]
    return crane.entityStore.load_or_create_all(entities)

def load_entity(entity, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    return crane.entityStore.load_or_create(entity)
    
# project(turtle) management APIs
def find_turtle(turtleScript):
    _turtle = crane.turtleStore.load_or_create(turtleScript)
    if _turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtleScript))
        return None
    return _turtle._id

def save_turtle(turtleId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        crane.turtleStore.save_one(_turtle)
        return True
    else:
        logger.error('failed to save turtle {0}'.format(turtleId))
        return False

def remove_turtle(turtleId):
    pass

def entity_collection(turtleId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.entityCollectionName
    else:
        logger.warning('can not find turtle {0} to get entity collection'.format(turtleId))
        return None
        
# training APIs
def add_data(turtleId, userId, ent):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        if not _turtle.has_user(userId):
            if _turtle.has_user_in_store(userId):
                _turtle.load_one(userId)
            else:
                _turtle.add_one(userId)
                _turtle.save_one(userId)
        ent = crane.entityStore.load_or_create(ent)
        return _turtle.add_data(userId, ent)
    else:
        logger.warning('can not find turtle by {0} to add data'.format(turtleId))
        return False

def train_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        if not _turtle.has_user(userId):
            if _turtle.has_user_in_store(userId):
                _turtle.load_one(userId)
            else:
                logger.warning('can not find user by {0} in turtle {1}'.format(userId, turtleId))
                return False
        _turtle.train_one(userId)
        _turtle.save_one(userId)
        return True
    else:
        logger.warning('can not find turtle by {0} to train'.format(turtleId))
        return False

def aggregate(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.aggregate(userId)
    else:
        logger.warning('can not find turtle by {0} to aggregate'.format(turtleId))
        return False
    
# testing APIs
def predict(turtleId, userId, entity):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.predict(userId, entity)
    else:
        logger.warning('can not find turtle by {0} to predict'.format(turtleId))
        return 0

# user APIs
def has_one_in_store(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.has_user_in_store(userId)
    else:
        logger.warning('can not find turtle by {0} to save a user'.format(turtleId))
        return False

def has_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.has_user(userId)
    else:
        logger.warning('can not find turtle by {0} to save a user'.format(turtleId))
        return False

def save_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.save_one(userId)
    else:
        logger.warning('can not find turtle by {0} to save a user'.format(turtleId))
        return False

def add_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.add_one(userId)
    else:
        logger.warning('can not find turtle by {0} to add a user'.format(turtleId))
        return False

def remove_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.remove_one(userId)
    else:
        logger.warning('can not find turtle by {0} to remove a user'.format(turtleId))
        return False

def load_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.load_one(userId)
    else:
        logger.warning('can not find turtle by {0} to load a user'.format(turtleId))
        return False

def unload_one(turtleId, userId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.unload_one(userId)
    else:
        logger.warning('can not find turtle by {0} to unload a user'.format(turtleId))
        return False
                
# meta query APIs
def find_type(typeName):
    return base.monkFactory.find(typeName)

def show_help():
    return {'help':'hello'}