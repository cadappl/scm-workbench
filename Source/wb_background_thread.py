'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_background_thread.py

'''
import threading

class BackgroundThread(threading.Thread):
    def __init__( self ):
        threading.Thread.__init__( self )
        self.setDaemon( 1 )
        self.running = 1

        self.work_queue = []
        self.queue_lock = threading.Lock()
        self.queued_work_semaphore = threading.Semaphore( 0 )

    def run( self ):
        while self.running:
            # wait for work
            self.queued_work_semaphore.acquire()

            # dequeue
            self.queue_lock.acquire()
            function = self.work_queue.pop( 0 )
            self.queue_lock.release()

            # run the function
            function()

        print 'BackgroundThread.run() shutdown'

    def addWork( self, function ):
        # queue the function
        self.queue_lock.acquire()
        self.work_queue.append( function )
        self.queue_lock.release()

        # count one more piece of work
        self.queued_work_semaphore.release()

    def shutdown( self ):
        self.addWork( self.__shutdown )

    def __shutdown( self ):
        self.running = 0
