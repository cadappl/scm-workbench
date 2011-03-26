'''
 ====================================================================
 Copyright (c) 2010 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_setting_dialog.py

'''

import re
import wx
import wb_exceptions
import os

import wb_torun_configspec
import wb_subversion_list_handler_common
import wb_shell_commands
import wb_dialogs
import wb_tree_panel
import wb_toolbars

class TorunSettingDialog( wx.Dialog ):
    def __init__( self, parent, app ):
        wx.Dialog.__init__( self, parent, -1, T_('Torun Settings'), size=(400,400) )
        self.app = app
        self.v_sizer = None

        # useful for debugging new pages
        try:
            self.initControls()
        except:
            app.log.exception( T_('TorunSettingDialog') )

        self.SetSizer( self.v_sizer )
        self.Layout()
        self.Fit()

        self.CentreOnParent()

    def initControls( self ):
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.notebook = wx.Notebook( self )

        self.v_sizer.Add( self.notebook, 0, wx.EXPAND|wx.ALL, 5 )

        self.pages = []
        self.pages.append( RepoListPage( self.notebook, self.app ) )
        self.pages.append( RepoSettingPage( self.notebook, self.app ) )
        self.pages.append( RepoPatternPage( self.notebook, self.app ) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( (1, 1), 1, wx.EXPAND )
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        for page in self.pages:
            if not page.validate():
                return

        for page in self.pages:
            page.savePreferences()

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

class PagePanel(wx.Panel):
    def __init__( self, notebook, title ):
        wx.Panel.__init__( self, notebook, -1, style = wx.NO_BORDER )

        self.page_v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.page_v_sizer.Add( self.initControls(), 1, wx.EXPAND|wx.ALL, 5 )
        self.SetSizer( self.page_v_sizer )
        self.SetAutoLayout( True )
        self.page_v_sizer.Fit( self )
        self.Layout()

        notebook.AddPage( self, title )

    def initControls( self ):
        raise wb_exceptions.InternalError('must override initControls')

    def validate( self ):
        return True

class RepoSettingPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Repository Path') )

    def initControls( self ):
        p = self.app.prefs.getRepository()

        self.grid_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )
        self.static_text1 = wx.StaticText( self, -1, T_('Baseline Repo: '), style=wx.ALIGN_RIGHT)
        self.text_ctrl_editor = wx.TextCtrl( self, -1, p.repo_baseline, wx.DefaultPosition, wx.Size( 300, -1 ) )

        self.browse_button = wx.Button( self, -1, T_(' Browse... '))

        self.grid_sizer.Add( self.static_text1, 0, wx.EXPAND|wx.ALL, 1 )
        self.grid_sizer.Add( self.text_ctrl_editor, 1, wx.EXPAND|wx.ALL, 1 )
        self.grid_sizer.Add( self.browse_button, 0, wx.EXPAND )

        self.static_text2 = wx.StaticText( self, -1, T_('Configspec Name: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_configspec = wx.TextCtrl( self, -1, p.repo_configspec, wx.DefaultPosition, wx.Size( 300, -1 ) )

        self.grid_sizer.Add( self.static_text2, 0, wx.EXPAND|wx.ALL, 1 )
        self.grid_sizer.Add( self.text_ctrl_configspec, 1, wx.EXPAND|wx.ALL, 1 )
        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )

        wx.EVT_BUTTON( self, self.browse_button.GetId(), self.OnBrowseExe )

        return self.grid_sizer

    def savePreferences( self ):
        p = self.app.prefs.getRepository()

        p.repo_baseline = self.text_ctrl_editor.GetValue().strip()
        p.repo_configspec = self.text_ctrl_configspec.GetValue().strip()

    def OnBrowseExe( self, event ):
        dir_dialog = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.text_ctrl_editor.SetValue( 'file:///%s' % dir_dialog.GetPath() )

        dir_dialog.Destroy()

class RepoListPage(PagePanel):
    class RepoListEditDialog(wx.Dialog):
        def __init__ ( self, parent, title, repo_name='', repo_dir='', edit_mode=False):
            wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE)
            self.static_text1 = wx.StaticText( self, -1, T_('Name:'), style=wx.ALIGN_RIGHT )

            self.edit_mode = edit_mode
            if edit_mode:
                self.static_repo = wx.StaticText( self, -1, repo_name )
            else:
                self.text_repo = wx.TextCtrl( self, -1, repo_name, wx.DefaultPosition, wx.Size(415, -1) )

            self.static_text2 = wx.StaticText( self, -1, T_('Location:'), style=wx.ALIGN_RIGHT )
            self.text_dir = wx.TextCtrl( self, -1, repo_dir, wx.DefaultPosition, wx.Size(415, -1) )

            gsizer = wx.FlexGridSizer( 0, 2, 0, 0 )
            gsizer.AddGrowableCol( 1 )

            gsizer.Add( self.static_text1, 1, wx.EXPAND|wx.ALL, 5 )
            if edit_mode:
                gsizer.Add( self.static_repo, 0, wx.EXPAND|wx.ALL, 5 )
            else:
                gsizer.Add( self.text_repo, 0, wx.EXPAND|wx.ALL, 5 )
            gsizer.Add( self.static_text2, 1, wx.EXPAND|wx.ALL, 5 )
            gsizer.Add( self.text_dir, 0, wx.EXPAND|wx.ALL, 5 )

            sizer = wx.BoxSizer( wx.VERTICAL )
            sizer.Add( gsizer )
            sizer.Add( wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL),
                       0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
            sizer.Add( self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL|wx.ALIGN_RIGHT, 5 )
            self.SetSizer( sizer )
            self.Fit()

        def GetValue( self ):
            if self.edit_mode:
                return self.text_dir.GetValue()
            else:
                return [ self.text_repo.GetValue(), self.text_dir.GetValue() ]

    def __init__( self, notebook, app ):
        self.app = app
        self.selected_name = None
        self.selected_item = None

        PagePanel.__init__( self, notebook, T_('Repository List') )

    def initControls( self ):
        self.p = self.app.prefs.getRepository()

        self.repo_map_list = wx.ListCtrl( self, -1, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT )
        self.repo_map_list.InsertColumn( 0, T_('Name') )
        self.repo_map_list.SetColumnWidth( 0, 100 )

        self.repo_map_list.InsertColumn( 1, T_('Location') )
        self.repo_map_list.SetColumnWidth( 1, 300 )

        repo_names = self.p.repo_map_list.keys()
        repo_names.sort( wb_torun_configspec.compare )
        for item in repo_names:
            index = self.repo_map_list.GetItemCount()
            self.repo_map_list.InsertStringItem( index, item )
            self.repo_map_list.SetStringItem( index, 1, self.p.repo_map_list[item] )

        self.button_add = wx.Button( self, -1, T_('Add ...') )
        self.button_remove = wx.Button( self, -1, T_('Remove') )
        self.button_remove.Enable( False )
        self.button_edit = wx.Button( self, -1, T_('Edit ...') )
        self.button_edit.Enable( False )
        self.button_import = wx.Button( self, -1, T_('Import ...') )
        self.button_export = wx.Button( self, -1, T_('Export ...') )

        # build the sizers
        button_sizer = wx.BoxSizer( wx.HORIZONTAL )
        button_sizer.Add( self.button_add, 0, wx.EXPAND|wx.ALL, 3 )
        button_sizer.Add( self.button_remove, 0, wx.EXPAND|wx.ALL, 3 )
        button_sizer.Add( self.button_edit, 0, wx.EXPAND|wx.ALL, 3 )
        button_sizer.Add( self.button_import, 0, wx.EXPAND|wx.ALL, 3 )
        button_sizer.Add( self.button_export, 0, wx.EXPAND|wx.ALL, 3 )

        self.sizer = wx.FlexGridSizer( 2, 1, 0, 0 )
        self.sizer.AddGrowableRow( 0 )
        self.sizer.AddGrowableCol( 0 )
        self.sizer.Add ( self.repo_map_list, 1, wx.EXPAND|wx.ALL, 1 )
        self.sizer.Add ( button_sizer, 0, wx.ALIGN_RIGHT )

        self.button_add.Bind( wx.EVT_BUTTON, self.OnButtonAdd )
        self.button_remove.Bind( wx.EVT_BUTTON, self.OnButtonRemove )
        self.button_edit.Bind( wx.EVT_BUTTON, self.OnButtonEdit )
        self.button_import.Bind( wx.EVT_BUTTON, self.OnButtonImport )
        self.button_export.Bind( wx.EVT_BUTTON, self.OnButtonExport )

        self.repo_map_list.Bind( wx.EVT_LEFT_DCLICK, self.OnButtonEdit )
        self.repo_map_list.Bind( wx.EVT_LIST_ITEM_SELECTED, self.OnRepoListSelected )
        self.repo_map_list.Bind( wx.EVT_LIST_ITEM_DESELECTED, self.OnRepoListDeselected )

        return self.sizer

    def OnRepoListSelected ( self, event ):
        self.button_remove.Enable( True )
        self.button_edit.Enable( True )
        self.selected_item = event.m_itemIndex

    def OnRepoListDeselected( self, event ):
        self.button_remove.Enable( False )
        self.button_edit.Enable( False )
        self.selected_item = None

    def OnButtonAdd( self, event ):
        repo_dialog = self.RepoListEditDialog( self, 'Add Repository Path')
        if repo_dialog.ShowModal() == wx.ID_OK:
            repo, dir = repo_dialog.GetValue()
            if self.p.repo_map_list.has_key( repo ):
                self._ReplaceContentInList( repo, dir )
            else:
                index = self.repo_map_list.GetItemCount()
                self.repo_map_list.InsertStringItem( index, repo )
                self.repo_map_list.SetStringItem( index, 1, dir )

            self.p.repo_map_list[repo] = dir

        repo_dialog.Destroy()

    def OnButtonEdit( self, event ):
        repo = self.repo_map_list.GetItem( self.selected_item, 0 ).GetText()
        dir = self.repo_map_list.GetItem( self.selected_item, 1 ).GetText()

        repo_dialog = self.RepoListEditDialog( self, 'Edit Repository Path', repo, dir, True )
        if repo_dialog.ShowModal() == wx.ID_OK:
            newdir = repo_dialog.GetValue()
            self._ReplaceContentInList( repo, newdir )
            self.p.repo_map_list[repo] = newdir

        repo_dialog.Destroy()

    def OnButtonRemove( self, event ):
        item = -1
        listp = list()
        while 1:
            item = self.repo_map_list.GetNextItem( item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED )
            if item == -1:
                break
            else:
                listp.append( item )

        listp.reverse()
        for k in listp:
            repo = self.repo_map_list.GetItem( k, 0 ).GetText()
            del self.p.repo_map_list[repo]
            self.repo_map_list.DeleteItem( k )

    def OnButtonImport( self, event):
        file_dialog = wx.FileDialog(
            self,
            T_('Open a repository mapping file'),
            style=wx.OPEN )

        if file_dialog.ShowModal() == wx.ID_OK:
            f = open( file_dialog.GetPath() )
            if f:
                for li in f:
                    li = li.strip()
                    if li[0] == ';' or li[0] == '#':
                        continue

                    parts = li.split()
                    if len(parts) < 2:
                        continue

                    repo, dir = parts[0], parts[1]
                    if self.p.repo_map_list.has_key( repo ):
                        self._ReplaceContentInList( repo, dir )
                    else:
                        index = self.repo_map_list.GetItemCount()
                        self.repo_map_list.InsertStringItem( index, repo )
                        self.repo_map_list.SetStringItem( index, 1, dir )

                    self.p.repo_map_list[repo] = dir
                f.close()

    def OnButtonExport( self, event):
        file_dialog = wx.FileDialog(
            self,
            T_('Select a repository mapping file'),
            style=wx.SAVE )

        if file_dialog.ShowModal() == wx.ID_OK:
            f = open( file_dialog.GetPath(), 'w' )
            if f:
                keys = self.p.repo_map_list.keys()
                keys.sort()
                for repo in keys:
                    f.write( '%s\t%s\n' % (repo, self.p.repo_map_list[repo]) )
                f.close()

    def _ReplaceContentInList( self, repo, dir):
        num = self.repo_map_list.GetItemCount()
        for k in xrange(0, num):
            item = self.repo_map_list.GetItem(k, 0)
            if item.GetText() == repo:
                self.repo_map_list.SetStringItem( k, 1, dir )
                break

    def savePreferences( self ):
        p = self.app.prefs.getRepository()

class RepoPatternPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Module Pattern') )

    def initControls( self ):
        p = self.app.prefs.getRepository()
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        # Add module info
        self.v_sizer_module = wx.StaticBoxSizer( wx.StaticBox( self, -1, T_('Module') ), wx.VERTICAL )

        self.g_sizer_pattern_module = wx.FlexGridSizer( 0, 4, 0, 0 )
        self.g_sizer_pattern_module.AddGrowableCol( 1 )
        self.g_sizer_pattern_module.AddGrowableCol( 3 )

        self.text_pattern_module = wx.StaticText( self, -1, T_('Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_pattern_module = wx.TextCtrl( self, -1, p.info_module.get( 'pattern', '') )
        self.text_parent_module = wx.StaticText( self, -1, T_('Parent Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_parent_module = wx.TextCtrl( self, -1, p.info_module.get( 'parent', '') )

        self.g_sizer_pattern_module.Add( self.text_pattern_module, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_module.Add( self.text_ctrl_pattern_module, 1, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_module.Add( self.text_parent_module, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_module.Add( self.text_ctrl_parent_module, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_module.Add( self.g_sizer_pattern_module, 1, wx.EXPAND|wx.ALL, 3 )

        self.g_sizer_component_module = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer_component_module.AddGrowableCol( 1 )
        self.text_component_module = wx.StaticText( self, -1, T_('Components: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_component_module = wx.TextCtrl( self, -1, p.info_module.get( 'component', '') )

        self.g_sizer_component_module.Add( self.text_component_module, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_component_module.Add( self.text_ctrl_component_module, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_module.Add( self.g_sizer_component_module, 1, wx.EXPAND|wx.ALL, 3 )

        self.v_sizer.Add( self.v_sizer_module, 1, wx.EXPAND|wx.ALL )

        # Add package info
        self.v_sizer_package = wx.StaticBoxSizer( wx.StaticBox( self, -1, T_('package') ), wx.VERTICAL )

        self.g_sizer_pattern_package = wx.FlexGridSizer( 0, 4, 0, 0 )
        self.g_sizer_pattern_package.AddGrowableCol( 1 )
        self.g_sizer_pattern_package.AddGrowableCol( 3 )

        self.text_pattern_package = wx.StaticText( self, -1, T_('Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_pattern_package = wx.TextCtrl( self, -1, p.info_package.get( 'pattern', '') )
        self.text_parent_package = wx.StaticText( self, -1, T_('Parent Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_parent_package = wx.TextCtrl( self, -1, p.info_package.get( 'parent', '') )

        self.g_sizer_pattern_package.Add( self.text_pattern_package, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_package.Add( self.text_ctrl_pattern_package, 1, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_package.Add( self.text_parent_package, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_package.Add( self.text_ctrl_parent_package, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_package.Add( self.g_sizer_pattern_package, 1, wx.EXPAND|wx.ALL, 1 )

        self.g_sizer_component_package = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer_component_package.AddGrowableCol( 1 )
        self.text_component_package = wx.StaticText( self, -1, T_('Components: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_component_package = wx.TextCtrl( self, -1, p.info_package.get( 'component', '') )

        self.g_sizer_component_package.Add( self.text_component_package, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_component_package.Add( self.text_ctrl_component_package, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_package.Add( self.g_sizer_component_package, 1, wx.EXPAND|wx.ALL, 1 )

        self.v_sizer.Add( self.v_sizer_package, 1, wx.EXPAND|wx.ALL )

        # Add project info
        self.v_sizer_project = wx.StaticBoxSizer( wx.StaticBox( self, -1, T_('project') ), wx.VERTICAL )

        self.g_sizer_pattern_project = wx.FlexGridSizer( 0, 4, 0, 0 )
        self.g_sizer_pattern_project.AddGrowableCol( 1 )
        self.g_sizer_pattern_project.AddGrowableCol( 3 )

        self.text_pattern_project = wx.StaticText( self, -1, T_('Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_pattern_project = wx.TextCtrl( self, -1, p.info_project.get( 'pattern', '') )
        self.text_parent_project = wx.StaticText( self, -1, T_('Parent Pattern: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_parent_project = wx.TextCtrl( self, -1, p.info_project.get( 'parent', '') )

        self.g_sizer_pattern_project.Add( self.text_pattern_project, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_project.Add( self.text_ctrl_pattern_project, 1, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_project.Add( self.text_parent_project, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_pattern_project.Add( self.text_ctrl_parent_project, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_project.Add( self.g_sizer_pattern_project, 1, wx.EXPAND|wx.ALL, 1 )

        self.g_sizer_component_project = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer_component_project.AddGrowableCol( 1 )
        self.text_component_project = wx.StaticText( self, -1, T_('Components: '), style=wx.ALIGN_RIGHT )
        self.text_ctrl_component_project = wx.TextCtrl( self, -1, p.info_project.get( 'component', '') )

        self.g_sizer_component_project.Add( self.text_component_project, 0, wx.EXPAND|wx.ALL, 1 )
        self.g_sizer_component_project.Add( self.text_ctrl_component_project, 1, wx.EXPAND|wx.ALL, 1 )
        self.v_sizer_project.Add( self.g_sizer_component_project, 1, wx.EXPAND|wx.ALL, 1 )

        self.v_sizer.Add( self.v_sizer_project, 1, wx.EXPAND|wx.ALL )
        self.v_sizer.Fit( self )

        return self.v_sizer

    def savePreferences( self ):
        p = self.app.prefs.getRepository()

        p.info_module['parent'] = self.text_ctrl_parent_module.GetValue().strip()
        p.info_module['pattern'] = self.text_ctrl_pattern_module.GetValue().strip()
        p.info_module['component'] = self.text_ctrl_component_module.GetValue().strip()

        p.info_package['parent'] = self.text_ctrl_parent_package.GetValue().strip()
        p.info_package['pattern'] = self.text_ctrl_pattern_package.GetValue().strip()
        p.info_package['component'] = self.text_ctrl_component_package.GetValue().strip()

        p.info_project['parent'] = self.text_ctrl_parent_project.GetValue().strip()
        p.info_project['pattern'] = self.text_ctrl_pattern_project.GetValue().strip()
        p.info_project['component'] = self.text_ctrl_component_project.GetValue().strip()
