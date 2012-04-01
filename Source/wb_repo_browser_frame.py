'''
 ====================================================================
 Copyright (c) 2010-2011 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_repo_browser_frame.py
'''

import sys
import time

import wx
import pysvn

import wb_images
import wb_exceptions
import wb_utils

ID_FILE = 0
ID_EXT  = 1
ID_REV  = 2
ID_AUTHOR = 3
ID_SIZE = 4
ID_DATE = 5

class RepoBrowserPanel( wx.Panel ):
    def __init__( self, parent, app, url='', updateUrl=None ):
        wx.Panel.__init__( self, parent, -1 )

        self.app = app
        self.parent = parent
        self.updateUrl = updateUrl

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        grid_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        grid_sizer.AddGrowableCol( 1 )

        grid_sizer.Add( wx.StaticText( self, -1, 'URL: ' ), 0, wx.EXPAND|wx.ALL, 3 )
        self.text_ctrl_url = wx.TextCtrl( self, -1, url, style=wx.TE_PROCESS_ENTER )
        grid_sizer.Add( self.text_ctrl_url, 1, wx.EXPAND|wx.ALL, 3 )
        self.button_browse = wx.Button( self, -1, '&Go' )
        grid_sizer.Add( self.button_browse, 0, wx.EXPAND|wx.ALL, 3 )
        v_sizer.Add( grid_sizer, 0, wx.EXPAND|wx.ALL )

        if 'wxMac' in wx.PlatformInfo:
            style = wx.SP_LIVE_UPDATE | wx.SP_3DSASH
        else:
            style = wx.SP_LIVE_UPDATE

        splitter = wx.SplitterWindow( self, -1, style=style )
        splitter.SetMinimumPaneSize( 100 )

        self.tree_ctrl = wx.TreeCtrl( splitter, -1 )
        self.list_ctrl = wx.ListCtrl( splitter, -1, style=wx.LC_REPORT )

        image_size = (16,16)
        self.il = wx.ImageList( *image_size )
        self.il_folder = self.il.Add( wx.ArtProvider.GetBitmap( wx.ART_FOLDER, size=image_size ) )
        self.il_file = self.il.Add( wx.ArtProvider.GetBitmap( wx.ART_NORMAL_FILE, size=image_size ) )
        self.tree_ctrl.SetImageList( self.il )
        self.list_ctrl.AssignImageList( self.il, wx.IMAGE_LIST_SMALL )

        splitter.SplitVertically( self.tree_ctrl, self.list_ctrl )

        v_sizer.Add( splitter, 1, wx.EXPAND|wx.ALL, 3 )
        self.SetSizer( v_sizer )

        self.init()

        wx.EVT_TEXT_ENTER( self, self.text_ctrl_url.GetId(), self.OnEventTextCtrlUrlEnter )
        wx.EVT_BUTTON( self, self.button_browse.GetId(), self.OnEventButtonBrowse )
        wx.EVT_TREE_SEL_CHANGED( self, self.tree_ctrl.GetId(), self.OnEventTreeCtrlChanged )
#        wx.EVT_LEFT_DCLICK( self, self.list_ctrl.GetId(), self.OnEventListCtrlDoubleClick )
        self.list_ctrl.Bind( wx.EVT_LEFT_DCLICK, self.OnEventListCtrlDoubleClick )
        self.list_ctrl.Bind( wx.EVT_LIST_ITEM_SELECTED, self.OnEventListCtrlSelected )

        self.updateControls()

    def init( self ):
        self.client = pysvn.Client()
        self.client.exception_style = 1
        self.client.commit_info_style = 1
        self.client.callback_get_login = wb_exceptions.TryWrapper( self.app.log, self.app.getCredentials )
        self.client.callback_ssl_server_trust_prompt = wb_exceptions.TryWrapper( self.app.log, self.getServerTrust )

        self.client.callback_notify = wb_exceptions.TryWrapper( self.app.log, self.app.log )

    def updateControls( self ):
        url = self.text_ctrl_url.GetValue().strip()

        if url:
            #yield self.app.backgroundProcess
            dir_status, self.all_files_status = self.getRepoStatus( url )
            #yield self.app.foregroundProcess

            self.tree_ctrl.DeleteAllItems()

            self.tree_item = self.tree_ctrl.AddRoot( dir_status[0].path )
            self.tree_ctrl.SetPyData( self.tree_item, dir_status[0] )

            self.tree_ctrl.SetItemImage( self.tree_item, self.il_folder, wx.TreeItemIcon_Normal )
            self.buildTreeItem( self.tree_item, dir_status[0].path )
            self.updateListItem( dir_status[0].path )

    def OnEventButtonBrowse( self, event ):
        dir_dialog = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.text_ctrl_url.SetValue( 'file:///%s' % dir_dialog.GetPath().replace( '\\', '/' ) )
            self.updateControls()

    def OnEventTextCtrlUrlEnter( self, event ):
        self.updateControls()

    def OnEventTreeCtrlChanged( self, event ):
        self.tree_item = event.GetItem()
        status = self.tree_ctrl.GetPyData( self.tree_item )

        self.updateListItem( status.path )

        if self.updateUrl is not None:
            self.updateUrl( status.path )

    def OnEventListCtrlDoubleClick( self, event ):
        dir_name = self.list_ctrl.GetItem( self.list_selected, ID_FILE ).GetText()

        self.updateTreeSelection( dir_name )

    def OnEventListCtrlSelected( self, event ):
        self.list_selected = event.m_itemIndex

    def getRepoStatus( self, url ):
        dir_status = None
        all_files_status = self.client.list( url, recurse=True )

        all_files_status.sort( wb_utils.by_list_path )

        if len( all_files_status) > 0:
            dir_status = all_files_status[0]
            del all_files_status[0]

        return dir_status, all_files_status

    def buildTreeItem( self, parent_item, dir_name ):
        name_len = len( dir_name ) + 1
        children = self._findChildren( dir_name, self.all_files_status, True )

        for c in children:
            name = c[0].path[name_len:]
            item = self.tree_ctrl.AppendItem( parent_item, name )
            self.tree_ctrl.SetPyData( item, c[0] )
            self.tree_ctrl.SetItemImage( item, self.il_folder, wx.TreeItemIcon_Normal )

            self.buildTreeItem( item, c[0].path )

    def updateTreeSelection( self, dir_name ):
        # find the node in tree
        item = self.tree_ctrl.GetRootItem()

        child_item, cookie = self.tree_ctrl.GetFirstChild( self.tree_item )
        while child_item:
            status = self.tree_ctrl.GetPyData( child_item )
            if status.path.endswith( dir_name ):
                self.tree_ctrl.SelectItem( child_item )
                break

            child_item, cookie = self.tree_ctrl.GetNextChild( child_item, cookie )

    def updateListItem( self, dir_name ):
        name_len = len( dir_name ) + 1
        children = self._findChildren( dir_name, self.all_files_status )

        self.list_ctrl.ClearAll()

        self.list_ctrl.InsertColumn( ID_FILE, 'File' )
        self.list_ctrl.InsertColumn( ID_EXT, 'Extension' )
        self.list_ctrl.InsertColumn( ID_REV, 'Revision' )
        self.list_ctrl.InsertColumn( ID_AUTHOR, 'Author' )
        self.list_ctrl.InsertColumn( ID_SIZE, 'Size', wx.LIST_FORMAT_RIGHT )
        self.list_ctrl.InsertColumn( ID_DATE, 'Date' )

        for id, c in enumerate(children):
            status = c[0]
            name = status.path[name_len:]
            if status.kind == pysvn.node_kind.dir:
                self.list_ctrl.InsertImageStringItem( id, name, self.il_folder )
            else:
                self.list_ctrl.InsertImageStringItem( id, name, self.il_file )

            off = name.rfind( '.' )
            if off != -1:
                extension = name[off + 1:]
                self.list_ctrl.SetStringItem( id, ID_EXT, extension )
            self.list_ctrl.SetStringItem( id, ID_AUTHOR, status.last_author )
            self.list_ctrl.SetStringItem( id, ID_SIZE, str( status.size ) )
            self.list_ctrl.SetStringItem( id, ID_DATE,
                                          time.strftime( '%Y-%m-%d %H:%M:%S', time.gmtime( int( status.time ) ) ) )
            self.list_ctrl.SetStringItem( id, ID_REV, str( status.created_rev.number ) )

#        self.list_ctrl.SetColumnWidth( ID_FILE, wx.LIST_AUTOSIZE )
#        self.list_ctrl.SetColumnWidth( ID_EXT, wx.LIST_AUTOSIZE )
#        self.list_ctrl.SetColumnWidth( ID_REV, wx.LIST_AUTOSIZE )
#        self.list_ctrl.SetColumnWidth( ID_AUTHOR, wx.LIST_AUTOSIZE )
#        self.list_ctrl.SetColumnWidth( ID_SIZE, wx.LIST_AUTOSIZE )
        self.list_ctrl.SetColumnWidth( ID_DATE, wx.LIST_AUTOSIZE )

    def getServerTrust( self, trust_data ):
        realm = trust_data['realm']

        info_list = []
        info_list.append( ( T_('Hostname'), trust_data['hostname']) )
        info_list.append( ( T_('Valid From'), trust_data['valid_from']) )
        info_list.append( ( T_('Valid Until'), trust_data['valid_until']) )
        info_list.append( ( T_('Issuer Name'), trust_data['issuer_dname']) )
        info_list.append( ( T_('Finger Print'), trust_data['finger_print']) )

        trust, save = self.app.getServerTrust( realm, info_list, True )
        return trust, trust_data['failures'], save

    def _findChildren( self, dir_name, all_files_status, isdir=False ):
        children = list()

        if not dir_name.endswith( '/' ):
            dir_name += '/'

        length = len( dir_name )
        for status in all_files_status:
            path = status[0].path
            if path.startswith( dir_name ) \
            and path[length:].find( '/' ) == -1 \
            and ( not isdir \
                or ( isdir and status[0].kind == pysvn.node_kind.dir ) ):
                children.append( status )

        return children

class RepoBrowserWindow:
    def __init__( self ):
        wx.EVT_CLOSE( self, self.OnCloseWindow )

        wx.EVT_SIZE( self, self.OnFrameSize )
        wx.EVT_MOVE( self, self.OnFrameMove )

    def OnCloseWindow( self, event ):
        repo_prefs = self.app.prefs.getRepoBrowser()
        # Size and Position are already saved
        repo_prefs.maximized = self.IsMaximized()

        self.Destroy()

    def OnFrameSize( self, event ):
        repo_prefs = self.app.prefs.getRepoBrowser()
        if not self.IsMaximized():
            repo_prefs.setFrameSize( self.GetSize() )

        event.Skip()

    def OnFrameMove( self, event ):
        repo_prefs = self.app.prefs.getRepoBrowser()
        if not self.IsMaximized() and not self.IsIconized():
            # don't use the event.GetPosition() as it
            # is off by the window frame thinkness
            pt = self.GetPosition()
            repo_prefs.frame_position = pt

        repo_prefs.maximized = self.IsMaximized()

        event.Skip()

    def OnZoomChange( self, evt ):
        zoom = evt.GetEventObject().GetZoom()
        self.SetZoom( zoom )
        repo_prefs = self.app.prefs.getRepoBrowser()
        repo_prefs.zoom = zoom

class RepoBrowserDialog( wx.Dialog, RepoBrowserWindow ):
    def __init__( self, parent, app, url ):

        self.app = app
        repo_prefs = self.app.prefs.getRepoBrowser()
        extra_style = 0
        if repo_prefs.maximized:
            extra_style = wx.MAXIMIZE

        wx.Dialog.__init__( self, parent, -1, 'Repository Dialog',
                  repo_prefs.frame_position, size=repo_prefs.getFrameSize(),
                  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|extra_style )

        RepoBrowserWindow.__init__( self )

        self.url = url

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( RepoBrowserPanel( self, app, url, self._updateUrl ), 1, wx.EXPAND|wx.ALL )
        v_sizer.Add( self.CreateStdDialogButtonSizer( wx.OK | wx.CANCEL ), 0, wx.EXPAND|wx.ALL, 5 )

        self.SetSizer( v_sizer )

    def _updateUrl( self, url ):
        self.url = url

    def getUrl( self ):
        return self.url

class RepoBrowserFrame( wx.Frame, RepoBrowserWindow ):
    def __init__( self, parent, app, url='' ):
        self.app = app
        repo_prefs = self.app.prefs.getRepoBrowser()

        extra_style = 0
        if repo_prefs.maximized:
            extra_style = wx.MAXIMIZE

        wx.Frame.__init__( self, parent, -1, 'Repository Browser',
                 repo_prefs.frame_position, repo_prefs.getFrameSize(),
                 style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER|extra_style )

        RepoBrowserWindow.__init__( self )
        self.SetIcon( wb_images.getIcon( 'wb.png') )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( RepoBrowserPanel( self, app, url ), 1, wx.EXPAND|wx.ALL )

        self.SetSizer( v_sizer )
