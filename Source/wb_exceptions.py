'''
 ====================================================================
 Copyright (c) 2003-2006 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_exceptions.py

'''
class WorkBenchError(Exception):
    def __init__( self, msg ):
        Exception.__init__( self, msg )

class InternalError(WorkBenchError):
    def __init__( self, msg ):
        WorkBenchError.__init__( self, msg )

#
#    Helper class to cut down code bloat.
#
#    in __init__ add:
#        self.try_wrapper = wb_exceptions.TryWrapperFactory( log )
#
#    where binding an EVT code as:
#
#        wxPython.wx.EVT_SIZE( self, self.try_wrapper( self.OnSize ) )
#
class TryWrapperFactory:
    def __init__( self, log ):
        self.log = log

    def __call__( self, function ):
        return TryWrapper( self.log, function, Exception )

class TryWrapperFactoryWithExcept:
    def __init__( self, log, excpt):
        self.log = log
        self.excpt = excpt

    def __call__( self, function ):
        return TryWrapper( self.log, function, self.excpt )

class TryWrapper:
    def __init__( self, log, function, excpt=Exception ):
        self.log = log
        self.excpt = excpt
        self.function = function

    def __call__( self, *params, **keywords ):
        try:
            result = self.function( *params, **keywords )
            return result
        except self.excpt, e:
            if hasattr( self.log, "exception" ):
                self.log.exception( 'TryWrapper<%s.%s>\n' %
                    (self.function.__module__, self.function.__name__ ) )
            else:
                print e
                self.log( e )

            return None
