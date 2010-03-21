'''
 ====================================================================
 Copyright (c) 2006 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_debug.py

'''
import inspect

def printStack( prefix='', depth=5 ):
    stack = inspect.stack()

    for caller in stack[1:depth]:
        print '%sFile: %s:%d, Function: %s' % (prefix, caller[1], caller[2], caller[3])
        del caller
    del stack
