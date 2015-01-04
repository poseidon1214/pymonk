# -*- coding: utf-8 -*-
"""
Created on Fri Dec 12 07:01:01 2014

@author: xm
"""

import monk.core.api as monkapi
from Queue import PriorityQueue
import time
import logging
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import tornado.httpserver
import tornado.ioloop
import tornado.web 
import simplejson
import traceback

logger = logging.getLogger('monk.network.server')

class TaskFactory(object):

    def __init__(self):
        self.factory = {}

    def register(self, TaskClass):
        className = TaskClass.__name__
        if className not in self.factory:
            self.factory[TaskClass.__name__] = TaskClass
 
    def find(self, name):
        return [key for key in self.factory.iterkeys() if key.find(name) >= 0]
        
    def create(self, message):
        try:
            generic = simplejson.loads(message)
            name = generic.get('op', None)
            if not name:
                return None
            else:
                return self.factory[name](generic)
        except Exception as e:
            logger.debug('can not create tasks for {}'.format(message))
            logger.debug('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            return None

taskFactory = TaskFactory()

def taskT(TaskClass):
    taskFactory.register(TaskClass)

@taskT
class Task(object):
    PRIORITY_HIGH = 1
    PRIORITY_LOW = 5
    FPRIORITY = 'priority'
    
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
        self.priority = int(decodedMessage.get(Task.FPRIORITY, Task.PRIORITY_LOW))
        self.name = self.decodedMessage.get('name')
        if self.name and isinstance(self.name, list):
            self.name = tuple(self.name)
    
    def info(self, logger, message):
        logger.info('{} for {}'.format(message, self.decodedMessage))
    
    def warning(self, logger, message):
        logger.warning('{} for {}'.format(message, self.decodedMessage))
    
    def error(self, logger, message):
        logger.error('{} for {}'.format(message, self.decodedMessage))
        
    def get(self, name, defaultValue=None):
        return self.decodedMessage.get(name, defaultValue)
        
    def act(self):
        self.warning(logger, 'no task is defined')

class MonkServer(object):    
    EXIT_WAIT_TIME=3
    MAX_QUEUE_SIZE=100000
    MAINTAIN_INTERVAL=10000
    POLL_INTERVAL=0.1
    EXECUTE_INTERVAL=0.1
    
    def __init__(self, serverName='', config=None):
        if not config:
            self.ready = False
            return
        self.pq = PriorityQueue(self.MAX_QUEUE_SIZE)
        self.serverName = serverName
        self.lastMaintenance = time.time()
        self.ioLoop = tornado.ioloop.IOLoop.instance()        
        self.httpServer = None
        self.port = 8888
        self.webApps = []
        self.brokers = self.init_brokers(config)
        if platform.system() == 'Windows':
            win32api.SetConsoleCtrlHandler(self._sig_handler, 1)
        else:
            signal.signal(signal.SIGINT,  self._sig_handler)
            signal.signal(signal.SIGTERM, self._sig_handler)
        self.ready = True
        
    def _sig_handler(self, sig, frame):
        logger.warning('Caught signal : {}'.format(sig))
        self.ioLoop.add_callback(self._onexit)
        
    def _onexit(self):
        logger.info('stopping the server {}'.format(self.serverName))
        if self.httpServer:
            self.httpServer.stop()
        logger.info('exit in {} seconds'.format(self.EXIT_WAIT_TIME))
        
        deadline = time.time() + self.EXIT_WAIT_TIME

        self.onexit()
        
        def stop_loop():
            now = time.time()
            if now < deadline and (self.ioLoop._callbacks or self.ioLoop._timeouts):
                self.ioLoop.add_timeout(now + 1, stop_loop)
            else:
                for broker in self.brokers:
                    broker.close()
                monkapi.exits()
                self.ioLoop.stop()
        stop_loop()
        
    def _maintain(self):
        self.maintain()
        self.ioLoop.add_timeout(self.MAINTAIN_INTERVAL, self.maintain)

    def _poll(self):
        if self.pq.full():
            self.ioLoop.add_timeout(self.POLL_INTERVAL, self._poll)
        else:
            taskScripts = filter(None, (broker.consume_one() for broker in self.brokers))
            for tscript in taskScripts:
                t = taskFactory.create(tscript)
                self.pq.put((t.priority, t), block=False)
            if taskScripts:
                self.ioLoop.add_callback(self._poll)
            else:
                self.ioLoop.add_timeout(self.POLL_INTERVAL, self._poll)
    
    def _execute(self):
        if self.pq.queue:
            priority, task = self.pq.get()
            task.act()
            self.ioLoop.add_callback(self._execute)
        else:
            self.ioLoop.add_timeout(self.EXECUTE_INTERVAL, self._execute)

    def add_application(self, regx, handler):
        self.webApps.append((regx, handler))
            
    def init_brokers(self, argvs):
        raise Exception('not implemented yet')
    
    def maintain(self):
        pass
    
    def onexit(self):
        pass

    def run(self):
        if not self.ready:
            logger.info('server {} is not intialized properly'.format(self.serverName))
            return
            
        self.ioLoop.add_timeout(self.MAINTAIN_INTERVAL, self._maintain)
        self.ioLoop.add_timeout(self.POLL_INTERVAL, self._poll)
        self.ioLoop.add_timeout(self.EXECUTE_INTERVAL, self._execute)
        
        if self.webApps:
            # fail immediately if http server can not run
            application = tornado.web.Application(self.webApps)
            self.httpServer = tornado.httpserver.HTTPServer(application)
            self.httpServer.listen(self.port)
        
        logger.info('{} is running'.format(self.schedulerName))        
        self.ioLoop.start()        
        logger.info('{} is exiting'.format(self.serverName))