#
#   wb_pychecker.py
#
#   helper to run pychecker on all the imports of workbench
#
import os
import sys
sys.path.insert( 0, os.environ['PYCHECKER_DIR'] )

class CountOutput:
    def __init__( self, f ):
        self.__f = f
        self.__write_count = 0
    def write( self, data ):
        self.__write_count += data.count('\n')
        return self.__f.write( data )

    def getWriteCount( self ):
        return self.__write_count

def report():
    count = sys.__stdout__.getWriteCount()
    print 'Info: %d lines' % count
    sys.exit( count != 0 )

os.environ['PYCHECKER'] = '--no-shadowbuiltin --config=./pycheckrc'
import pychecker.checker

sys.__stdout__ = CountOutput( sys.__stdout__ )
sys.stdout = sys.__stdout__

import wb_main
