'''
 ====================================================================
 Copyright (c) 2003-2006 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_provider.py

'''
import os
import time
import fnmatch
import pysvn
import threading
import wx
import wb_source_control_providers
import wb_subversion_history
import wb_subversion_annotate
import wb_ids
import wb_exceptions
import wb_subversion_tree_handler
import wb_subversion_list_handler
import wb_subversion_utils
import wb_subversion_project_info

def registerProvider():
    wb_source_control_providers.registerProvider( SubversionProvider() )

class SubversionProvider(wb_source_control_providers.Provider):
    def __init__( self ):
        wb_source_control_providers.Provider.__init__( self, 'subversion' )

    def getProjectInfo( self, app, parent=None ):
        return wb_subversion_project_info.ProjectInfo( app, parent )

    def getUpdateProjectDialog( self, app, parent, project_info ):
        return wb_subversion_project_info.UpdateProjectDialog( app, parent, project_info )

    def getProjectTreeItem( self, app, project_info ):
        return wb_subversion_tree_handler.SubversionProject( app, project_info )

    def getListHandler( self, app, list_panel, project_info ):
        return wb_subversion_list_handler.SubversionListHandler( app, list_panel, project_info )

    def getAboutString( self ):
        return ('pysvn version: %d.%d.%d-%d\n'
            'svn version: %d.%d.%d-%s\n' %
                (pysvn.version[0], pysvn.version[1],
                 pysvn.version[2], pysvn.version[3],
                 pysvn.svn_version[0], pysvn.svn_version[1],
                 pysvn.svn_version[2], pysvn.svn_version[3]) )

