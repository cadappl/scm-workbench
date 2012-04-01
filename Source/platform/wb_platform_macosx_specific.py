'''

 ====================================================================
 Copyright (c) 2004-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_macosx_specific.py

'''
import os
import types

def getApplicationDir():
    return os.path.join( os.environ['HOME'], 'Library/Preferences/org.tigris.pysvn.Workbench' )

def getLocalePath( app ):
    return os.path.join( os.environ.get( 'PYTHONHOME', app.app_dir ), 'locale' )

def getNullDevice():
    return '/dev/null'

def uPathExists( path ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return os.path.exists( path )

def uPathIsdir( path ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return os.path.isdir( path )

def uAccess( path, mode ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return os.access( path, mode )

def uRemove( path ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return os.remove( path )

def uRename( path1, path2 ):
    if type(path1) == types.UnicodeType:
        path1 = path1.encode( 'utf-8' )

    if type(path2) == types.UnicodeType:
        path2 = path2.encode( 'utf-8' )

    return os.rename( path1, path2 )

def uOpen( path, mode ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return open( path, mode )

def uChdir( path ):
    if type(path) == types.UnicodeType:
        path = path.encode( 'utf-8' )

    return os.chdir( path )
