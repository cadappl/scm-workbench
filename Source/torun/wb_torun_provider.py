'''
 ====================================================================
 Copyright (c) 2010 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_provider.py

'''

import wb_torun_project_info
import wb_torun_tree_handler
import wb_torun_list_handler
import wb_torun_setting_panels

import wb_subversion_project_info
import wb_source_control_providers
import wb_torun_project_dialogs

def registerProvider():
    wb_source_control_providers.registerProvider( TorunProvider() )

class TorunProvider(wb_source_control_providers.Provider):
    def __init__( self ):
        wb_source_control_providers.Provider.__init__( self, 'torun' )

    def getProjectInfo( self, app, parent=None ):
        return wb_torun_project_info.ProjectInfo( app, parent )

    def getUpdateProjectDialog(self, app, parent, project_info):
        return wb_torun_project_info.UpdateProjectDialog(app, parent, project_info )

    def getProjectTreeItem( self, app, project_info ):
        return wb_torun_tree_handler.TorunProject( app, project_info )

    def getListHandler( self, app, list_panel, project_info ):
        return wb_torun_list_handler.TorunListHandler( app, list_panel, project_info )

    def getPreferencePanels( self ):
        return ( wb_torun_setting_panels.RepoSettingPage,
                 wb_torun_setting_panels.RepoListPage,
                 wb_torun_setting_panels.RepoPatternPage )

    def getProjectDialog( self ):
        return wb_torun_project_dialogs.AddProjectDialog

    def getAboutString( self ):
        return ('TORUN version: 1.1\n'
            'configspec version: %s\n' % wb_configspec.__version__)
