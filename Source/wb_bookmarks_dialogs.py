'''
 ====================================================================
 Copyright (c) 2005-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_bookmarks_dialogs.py

'''
import wx
import string
import wb_exceptions

#
# all dialog changes are recorded in the BookmarkProperties
# object when the user clicks OK the changes are set into the
# preferences. Cancel leaves the preferences unchanged.
#
class BookmarkProperties:
    def __init__( self, pi ):
        self.pi = pi
        self.wc_path = pi.wc_path
        self.menu_name = pi.menu_name
        self.menu_folder = pi.menu_folder
        self.menu_folder2 = pi.menu_folder2
        self.menu_folder3 = pi.menu_folder3

        self.updated()

    def updated( self ):
        self.menu_list = _keyBookmarks( self )
        while len( self.menu_list ) < 4:
            self.menu_list.append( '' )

def _keyBookmarks( a ):
    k = []
    if a.menu_folder != '':
        k.append( a.menu_folder )
    if a.menu_folder2 != '':
        k.append( a.menu_folder2 )
    if a.menu_folder3 != '':
        k.append( a.menu_folder3 )
    k.append( a.menu_name )

    return k

class BookmarkManageDialog(wx.Dialog):
    COL_MENU1 = 0
    COL_MENU2 = 1
    COL_MENU3 = 2
    COL_MENU4 = 3
    COL_WC_PATH = 4

    def __init__( self, parent, app, bookmark_prefs ):
        wx.Dialog.__init__( self, parent, -1, T_("Manage Bookmarks") )
        self.app = app

        self.bookmark_prefs = bookmark_prefs

        self.initControls()

    def initControls( self ):
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer1 = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer2 = wx.BoxSizer( wx.HORIZONTAL )
        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.bookmark_list_ctrl = BookmarkListCtrl( self )
        self.bookmark_list_ctrl.InsertColumn( self.COL_MENU1, T_("Menu") )
        self.bookmark_list_ctrl.InsertColumn( self.COL_MENU2, T_("Menu") )
        self.bookmark_list_ctrl.InsertColumn( self.COL_MENU3, T_("Menu") )
        self.bookmark_list_ctrl.InsertColumn( self.COL_MENU4, T_("Menu") )
        self.bookmark_list_ctrl.InsertColumn( self.COL_WC_PATH, T_("WC Path") )
        self.bookmark_list_ctrl.SetColumnWidth( self.COL_MENU1, 150 )
        self.bookmark_list_ctrl.SetColumnWidth( self.COL_MENU2, 150 )
        self.bookmark_list_ctrl.SetColumnWidth( self.COL_MENU3, 150 )
        self.bookmark_list_ctrl.SetColumnWidth( self.COL_MENU4, 150 )
        self.bookmark_list_ctrl.SetColumnWidth( self.COL_WC_PATH, 600 )

        self.all_bookmark_props = [BookmarkProperties( self.bookmark_prefs.getBookmark( name ) )
                                        for name in self.bookmark_prefs.getBookmarkNames()
                                            if name != 'last position']
        self.sortBookmarks()

        self.bookmark_deleted_list = []

        self.bookmark_list_ctrl.SetItemCount( len( self.all_bookmark_props ) )

        self.button_delete = wx.Button( self, wx.NewId(), T_(" Delete ") )
        self.button_delete.Enable( False )

        self.button_props = wx.Button( self, wx.NewId(), T_(" Properties ") )
        self.button_props.Enable( False )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(" OK ") )
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(" Cancel ") )
        self.button_ok.SetDefault()

        self.h_sizer1.Add( self.button_props, 0, wx.EXPAND|wx.WEST, 15)
        self.h_sizer1.Add( self.button_delete, 0, wx.EXPAND|wx.WEST, 15)
        self.h_sizer1.Add( (60, 20), 1, wx.EXPAND)

        self.h_sizer2.Add( (60, 20), 1, wx.EXPAND)
        self.h_sizer2.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15)
        self.h_sizer2.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.g_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.bookmark_list_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer1, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer2, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        wx.EVT_LIST_ITEM_ACTIVATED( self, self.bookmark_list_ctrl.GetId(), try_wrapper( self.OnActivateBookmark ) )
        wx.EVT_LIST_ITEM_SELECTED( self, self.bookmark_list_ctrl.GetId(), try_wrapper( self.OnSelectBookmark ) )
        wx.EVT_LIST_ITEM_DESELECTED( self, self.bookmark_list_ctrl.GetId(), try_wrapper( self.OnDeselectBookmark ) )

        wx.EVT_BUTTON( self, self.button_delete.GetId(), try_wrapper( self.OnDeleteBookmark ) )
        wx.EVT_BUTTON( self, self.button_props.GetId(), try_wrapper( self.OnPropertiesBookmark ) )
        wx.EVT_BUTTON( self, wx.ID_OK, try_wrapper( self.OnOk ) )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, try_wrapper( self.OnCancel ) )

    def sortBookmarks( self ):
        self.all_bookmark_props.sort( key=_keyBookmarks )

    def OnGetItemText( self, item, col ):
        props = self.all_bookmark_props[ item ]
        if col in [self.COL_MENU1, self.COL_MENU2, self.COL_MENU3, self.COL_MENU4]:
            return props.menu_list[ col ]

        elif col == self.COL_WC_PATH:
            return props.wc_path

        else:
            return ''

    def OnGetItemImage( self, item ):
        return -1

    def OnGetItemAttr( self, item ):
        return None

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def OnActivateBookmark( self, event ):
        self.OnSelectBookmark( event )
        self.OnPropertiesBookmark( event )

    def OnSelectBookmark( self, event ):
        self.button_delete.Enable( True )
        self.button_props.Enable( True )

    def OnDeselectBookmark( self, event ):
        if self.bookmark_list_ctrl.GetNextSelected(-1) < 0:
            self.button_delete.Enable( False )
            self.button_props.Enable( False )

    def OnDeleteBookmark( self, event ):
        # delete all selected bookmarks.
        bookmark_index = -1
        selected_bookmarks = []
        while True:
            bookmark_index = self.bookmark_list_ctrl.GetNextSelected( bookmark_index )
            if bookmark_index < 0:
                break
            selected_bookmarks.append( bookmark_index )
        for bookmark_index in reversed( selected_bookmarks ):
            self.bookmark_deleted_list.append( self.all_bookmark_props.pop( bookmark_index ) )

        # if there is a bookmark left after the last deletion,
        # select it, so pressing delete multiple times works.
        if len( self.all_bookmark_props ) > 0:
            self.bookmark_list_ctrl.Select( bookmark_index )
            self.bookmark_list_ctrl.SetItemCount( len( self.all_bookmark_props ) )
            self.bookmark_list_ctrl.RefreshItems( 0, len( self.all_bookmark_props )-1 )
        else:
            self.button_delete.Enable( False )
            self.button_props.Enable( False )
            self.bookmark_list_ctrl.SetItemCount( 0 )

    def OnPropertiesBookmark( self, event ):
        refresh_list = False
        bookmark_index = -1
        while True:
            bookmark_index = self.bookmark_list_ctrl.GetNextSelected( bookmark_index )
            if bookmark_index < 0:
                break
            dialog = BookmarkPropertiesDialog( self, self.app, self.all_bookmark_props[ bookmark_index ] )

            rc = dialog.ShowModal()
            if rc == wx.ID_OK:
                refresh_list = True

        if refresh_list:
            self.sortBookmarks()
            self.bookmark_list_ctrl.RefreshItems( 0, len( self.all_bookmark_props )-1 )

    def setPreferences( self ):
        for props in self.getDeletedBookmarkList():
            self.bookmark_prefs.delBookmark( props.wc_path )

        for props in self.all_bookmark_props:
            props.pi.menu_name = props.menu_name
            props.pi.menu_folder = props.menu_folder
            props.pi.menu_folder2 = props.menu_folder2
            props.pi.menu_folder3 = props.menu_folder3

    def getDeletedBookmarkList( self ):
        return self.bookmark_deleted_list

class BookmarkListCtrl(wx.ListCtrl):
    def __init__( self, parent ):
        wx.ListCtrl.__init__( self, parent, -1,
                                size=(700,400),
                                style=wx.LC_REPORT|wx.LC_VIRTUAL )
        self.parent = parent

    def OnGetItemText( self, item, col ):
        return self.parent.OnGetItemText( item, col )

    def OnGetItemImage( self, item ):
        return self.parent.OnGetItemImage( item )

    def OnGetItemAttr( self, item ):
        return self.parent.OnGetItemAttr( item )

class BookmarkPropertiesDialog(wx.Dialog):
    def __init__( self, parent, app, props ):
        wx.Dialog.__init__( self, parent, -1, T_("Bookmark Properties") )

        self.parent = parent
        self.app = app
        self.props = props

        self.initControls()

    def initControls( self ):
        all_menu_folders1 = set( [prop.menu_folder  for prop in self.parent.all_bookmark_props] )
        all_menu_folders2 = set( [prop.menu_folder2 for prop in self.parent.all_bookmark_props] )
        all_menu_folders3 = set( [prop.menu_folder3 for prop in self.parent.all_bookmark_props] )

        all_menu_folders = set()
        all_menu_folders |= all_menu_folders1
        all_menu_folders |= all_menu_folders2
        all_menu_folders |= all_menu_folders3
        all_menu_folders = sorted( all_menu_folders, key=string.lower )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer2 = wx.BoxSizer( wx.HORIZONTAL )
        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.wc_path_ctrl = wx.TextCtrl( self, -1, self.props.wc_path, size=(500, -1), style=wx.TE_READONLY )

        self.menu_folder1_ctrl = wx.ComboBox( self, -1, self.props.menu_folder,
                                                style=wx.CB_DROPDOWN, choices=all_menu_folders,
                                                size=(300, -1) )

        self.menu_folder2_ctrl = wx.ComboBox( self, -1, self.props.menu_folder2,
                                                style=wx.CB_DROPDOWN, choices=all_menu_folders,
                                                size=(300, -1) )

        self.menu_folder3_ctrl = wx.ComboBox( self, -1, self.props.menu_folder3,
                                                style=wx.CB_DROPDOWN, choices=all_menu_folders,
                                                size=(300, -1) )

        self.menu_name_ctrl = wx.TextCtrl( self, -1, self.props.menu_name, size=(300, -1) )
        self.menu_name_ctrl.SetFocus()
        self.menu_name_ctrl.SetSelection( -1, -1 )

        self.static_text1 = wx.StaticText( self, -1, T_("WC Path: "), style=wx.ALIGN_RIGHT)
        self.g_sizer.Add( self.static_text1, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.wc_path_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.static_text3 = wx.StaticText( self, -1, T_("Menu1: "), style=wx.ALIGN_RIGHT)
        self.g_sizer.Add( self.static_text3, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.menu_folder1_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.static_text4 = wx.StaticText( self, -1, T_("Menu2: "), style=wx.ALIGN_RIGHT)
        self.g_sizer.Add( self.static_text4, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.menu_folder2_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.static_text5 = wx.StaticText( self, -1, T_("Menu3: "), style=wx.ALIGN_RIGHT)
        self.g_sizer.Add( self.static_text5, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.menu_folder3_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.static_text2 = wx.StaticText( self, -1, T_("Menu Name: "), style=wx.ALIGN_RIGHT)
        self.g_sizer.Add( self.static_text2, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.menu_name_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(" OK ") )
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(" Cancel ") )
        self.button_ok.SetDefault()

        self.h_sizer2.Add( (60, 20), 1, wx.EXPAND)
        self.h_sizer2.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15)
        self.h_sizer2.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.g_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer2, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        wx.EVT_BUTTON( self, wx.ID_OK, try_wrapper( self.OnOk ) )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, try_wrapper( self.OnCancel ) )

    def updateProps( self ):
        self.props.menu_name = self.menu_name_ctrl.GetValue()
        self.props.menu_folder = self.menu_folder1_ctrl.GetValue()
        self.props.menu_folder2 = self.menu_folder2_ctrl.GetValue()
        self.props.menu_folder3 = self.menu_folder3_ctrl.GetValue()
        self.props.updated()

    def OnOk( self, event ):
        self.updateProps()
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )
