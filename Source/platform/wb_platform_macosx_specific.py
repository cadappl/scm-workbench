'''

 ====================================================================
 Copyright (c) 2004-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_macosx_specific.py

'''
import os
import sys

def getApplicationDir():
    return os.path.join( os.environ['HOME'], 'Library/Preferences/org.tigris.pysvn.Workbench' )

def getLocalePath( app ):
    return os.path.join( os.environ.get( 'PYTHONHOME', app.app_dir ), 'locale' )

def getNullDevice():
    return '/dev/null'
