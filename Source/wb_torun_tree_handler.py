'''
 ====================================================================
 Copyright (c) 2010 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_tree_handler.py

'''

import os
import wx
import pysvn

import wb_ids
import wb_config
import wb_subversion_utils

import wb_subversion_tree_handler
import wb_subversion_project_info

class TorunProject(wb_subversion_tree_handler.SubversionProject):
    def __init__( self, app, project_info ):
        wb_subversion_tree_handler.SubversionProject.__init__( self, app, project_info )

    def getContextMenu( self, state ):
        menu_item =[('', wb_ids.id_Command_Shell, T_('&Command Shell') )
            ,('', wb_ids.id_File_Browser, T_('&File Browser') )
            ,('-', 0, 0 )]

        if self.project_info.need_checkout:
            menu_item += [('', wb_ids.id_SP_Checkout, T_('Checkout') )]
        if self.project_info.need_update or (not self.project_info.need_checkout):
            menu_item += [('', wb_ids.id_SP_Update, T_('Update') )]

        return wb_subversion_utils.populateMenu( wx.Menu(), menu_item )

    def getExpansion( self ):
        project_info_list = []

        for file in self.project_info.getTreeFilesStatus():

            if( (file.entry is None and os.path.isdir( file.path ))
            or (file.entry is not None and file.entry.kind == pysvn.node_kind.dir) ):
                pi = wb_subversion_project_info.ProjectInfo( self.app, self.project_info )
                name = os.path.basename( file.path )
                if file.entry is None or file.entry.url is None:
                    url = '%s/%s' % (self.project_info.url, name )
                else:
                    url = file.entry.url

                # use default subversion clients instead of the ones in ProjectInfo for Torun
                pi.init( name, url=url, wc_path=file.path, menu_info=self.project_info.menu_info)
                project_info_list.append( pi )

        return project_info_list

    def getTreeNodeColour( self ):
        if self.project_info.need_checkout:
            return wb_config.colour_status_need_checkout
        else:
            return wb_config.colour_status_normal
