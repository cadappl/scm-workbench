'''
 ====================================================================
 Copyright (c) 2011 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_utils.py

'''

import os
import re
import sys

def compare( x, y ):
    (ax, bx, ay, by) = (x, y, '0', '0')
    mx = re.match( '([^0-9]+)([0-9]+)', x )
    if mx: ax, ay = mx.group(1), mx.group(2)
    my = re.match( '([^0-9]+)([0-9]+)', y )
    if my: bx, by = my.group(1), my.group(2)

    if cmp( ax, bx ) == 0:
        try:
            return int( ay, 10 ) - int( by, 10 )
        except:
            return 0
    else:
        return cmp( ax, bx )

def formatPath( path ):
    path = path.replace( '\\', '/' )
    if path.endswith( '/' ):
        path = path[:-1]

    return path.replace( '//', '/' )

def __loadFile( path, module, interf ):
    #try:
        sys.path.append( path )
        mo = __import__( module, globals() )
        reload( mo )

        getattr( mo, interf )()
    #except:
    #    print "Error to load %s in %s" % ( module, path )
    #    sys.path.pop( -1 )

def loadExts( dirp ):
    listp = os.listdir( dirp )

    # re-order the directory 'manifest' to the beginning of the list
    if 'manifest' in listp:
        listp.remove( 'manifest' )
        listp.insert( 0, 'manifest' )

    for d in listp:
        path = os.path.join( dirp, d )
        if d != None and d[0] != '.' and os.path.isdir( path ):
            files = os.listdir( path )

            registered = list()
            # check the file with postfix "_provider"
            for f in files:
                main, ext = os.path.splitext( f )
                # use registered to avoid reload
                if main in registered:
                    continue

                if ext.startswith( '.py' ) and main.endswith( '_provider' ):
                    __loadFile( path, main, 'registerProvider' )
                    registered.append( main )

def by_list_path( a, b ):
    return cmp( a[0].path, b[0].path )

def handleMenuInfo( project_info, start=0 ):
    menu_context = list()

    length = len( project_info.menu_info or list() )
    while start < length:
        id, func, callback = project_info.menu_info[start]
        # optimized for separator
        if id == 0 or func == None:
            menu_tmp = handleMenuInfo( project_info, start + 1 )
            if len(menu_tmp):
                menu_context.append( ( '-', 0, 0 ) )
                menu_context += menu_tmp
                break
        else:
            ret, context = func( project_info )
            if ret:
                menu_context.append( ( '', id, context) )

        start += 1

    return menu_context

