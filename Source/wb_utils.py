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

import wx

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

def _getSplitVersionNumber( version ):
    # skip the package nanme if it has
    if version.find( '-' ):
        version = ( version.split( '-' ) )[1]

    return version.split( '.' )

def _getInteger( value ):
    val = 0
    handled = False
    for v in value:
        if '0' <= v <= '9':
            handled = True
            val = val * 10 + int(v)
    
    if handled:
        return val
    else:
        return value
    
def compareVersion( x, y ):
    vx = _getSplitVersionNumber( x )
    vy = _getSplitVersionNumber( y )
    
    length = len( vx )
    if len( vy ) < length: length = len( vy )    

    for k in range(length):
        z = cmp( _getInteger( vx[k] ), _getInteger( vy[k] ) )
        if z != 0:
            return z
    
    return cmp( len( vx ), len( vy ) )

def formatPath( path ):
    if path == None:
        return None

    schema = '://'
    path = path.replace( '\\', '/' )

    segments = path.split( schema, 1 )
    if len( segments ) > 1:
        segments[1] = segments[1].replace( '//', '/' )

    path = schema.join( segments )
    if path.endswith( '/' ):
        path = path[:-1]

    return path

def __loadFile( path, module, interf ):
    try:
        # print path, module, interf
        sys.path.append( path )
        mo = __import__( module, globals() )
        reload( mo )

        getattr( mo, interf )()
    except:
        print "Error to load %s in %s" % ( module, path )
        sys.path.pop( -1 )

def loadExts( dirp ):
    listp = os.listdir( dirp )

    # re-order the directory 'manifest' to the beginning of the list
    listp.sort()
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

def by_path( a, b ):
    return compare( a.path, b.path )

def by_list_path( a, b ):
    return compare( a[0].path, b[0].path )

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

def populateMenu( menu, contents ):
    separator = False
    for details in contents:
        if len(details) == 3:
            type, id, name = details
            cond = True
        else:
            type, id, name, cond = details

        if type == '-':
            if cond and ( not separator ):
                separator = True
                menu.AppendSeparator()
        else:
            separator = False
            if type == 'x':
                menu.AppendCheckItem( id, name )
                menu.Enable( id, cond )
            elif type == 'o':
                menu.AppendRadioItem( id, name )
                menu.Enable( id, cond )
            elif type == '':
                menu.Append( id, name )
                menu.Enable( id, cond )
            elif type == '>':
                # sub menu in the list in id
                menu.AppendMenu( id, name, populateMenu( wx.Menu(), cond ) )
            else:
                raise wb_exceptions.InternalError(
                    'Unknown populateMenu contents (%s,%s,%s,%s)' %
                        (repr(type),repr(id),repr(name),repr(cond)) )
    return menu
