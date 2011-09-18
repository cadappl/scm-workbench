'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2011 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_setting_panels.py

'''

import wx
import wb_preferences_dialog
import wb_subversion_list_handler_common

class ListColumnsPage(wb_preferences_dialog.PagePanel):
    id_exclude = wx.NewId()
    id_include = wx.NewId()
    id_move_up = wx.NewId()
    id_move_down = wx.NewId()
    id_excluded_list = wx.NewId()
    id_included_list = wx.NewId()
    id_width = wx.NewId()

    def __init__( self, notebook, app ):
        self.app = app
        self.selected_col_id = None
        self.column_info = wb_subversion_list_handler_common.ViewColumnInfo()
        wb_preferences_dialog.PagePanel.__init__( self, notebook, T_('Columns') )

    def initControls( self ):
        p = self.app.prefs.getView()
        self.column_info.setFromPreferenceData( p )

        self.excluded_list = wx.ListCtrl( self, ListColumnsPage.id_excluded_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.excluded_list.InsertColumn( 0, T_('Column') )
        self.excluded_list.SetColumnWidth( 0, 100 )
        self.excluded_list.InsertColumn( 1, T_('Width'), wx.LIST_FORMAT_RIGHT )
        self.excluded_list.SetColumnWidth( 1, 80 )

        self.included_list = wx.ListCtrl( self, ListColumnsPage.id_included_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.included_list.InsertColumn( 0, T_('Column') )
        self.included_list.SetColumnWidth( 0, 100 )
        self.included_list.InsertColumn( 1, T_('Width'), wx.LIST_FORMAT_RIGHT )
        self.included_list.SetColumnWidth( 1, 80 )

        for name in self.column_info.getColumnOrder():
            info = self.column_info.getInfoByName( name )
            info.included =  True
            index = self.included_list.GetItemCount()

            self.included_list.InsertStringItem( index, T_( info.label ) )
            self.included_list.SetItemData( index, info.col_id )
            self.included_list.SetStringItem( index, 1, str(info.width) )

        for info in self.column_info.excludedInfo():
            index = self.excluded_list.GetItemCount()

            self.excluded_list.InsertStringItem( index, T_( info.label ) )
            self.excluded_list.SetItemData( index, info.col_id )
            self.excluded_list.SetStringItem( index, 1, str(info.width) )


        self.button_include = wx.Button( self, ListColumnsPage.id_include, T_(' Include --> ') )
        self.button_include.Enable( False )
        self.button_exclude = wx.Button( self, ListColumnsPage.id_exclude, T_(' <-- Exclude ') )
        self.button_exclude.Enable( False )

        self.button_up = wx.Button( self, ListColumnsPage.id_move_up, T_(' Move Up ') )
        self.button_up.Enable( False )
        self.button_down = wx.Button( self, ListColumnsPage.id_move_down, T_(' Move Down ') )
        self.button_down.Enable( False )

        self.width_text_ctrl = wx.TextCtrl( self, ListColumnsPage.id_width, '',
                wx.DefaultPosition, wx.Size(200, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT  )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.button_include, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_exclude, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.width_text_ctrl, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_up, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_down, 0, wx.EXPAND|wx.EAST, 5 )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( self.excluded_list, 0, wx.EXPAND|wx.WEST, 5 )
        self.h_sizer.Add( self.v_sizer, 0, wx.EXPAND|wx.EAST, 5 )
        self.h_sizer.Add( self.included_list, 0, wx.EXPAND|wx.EAST, 5 )

        wx.EVT_BUTTON( self, ListColumnsPage.id_include, self.OnInclude )
        wx.EVT_BUTTON( self, ListColumnsPage.id_exclude, self.OnExclude )
        wx.EVT_BUTTON( self, ListColumnsPage.id_move_up, self.OnMoveUp )
        wx.EVT_BUTTON( self, ListColumnsPage.id_move_down, self.OnMoveDown )

        wx.EVT_TEXT_ENTER( self, ListColumnsPage.id_width, self.OnWidthTextEnter )

        wx.EVT_LIST_ITEM_SELECTED( self, ListColumnsPage.id_excluded_list, self.OnExcludedListItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ListColumnsPage.id_excluded_list, self.OnExcludedListItemDeselected )

        wx.EVT_LIST_ITEM_SELECTED( self, ListColumnsPage.id_included_list, self.OnIncludedListItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ListColumnsPage.id_included_list, self.OnIncludedListItemDeselected )

        return self.h_sizer

    def OnInclude( self, event ):
        self.changeInclusionColumn( True, self.excluded_list, self.included_list )

    def OnExclude( self, event ):
        self.changeInclusionColumn( False, self.included_list, self.excluded_list )

    def changeInclusionColumn( self, include, from_list, to_list ):
        info = self.column_info.getInfoById( self.selected_col_id )

        try:
            width = int(self.width_text_ctrl.GetValue())
        except ValueError:
            wx.MessageBox( T_('Width for %(name)s must be an number between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        if( width >= info.min_width
        and width <= info.max_width ):
            info.width = width
        else:
            wx.MessageBox( T_('Width for %(name)s must be between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        info.include = include

        # remove from from_list
        from_index = from_list.FindItemData( -1, info.col_id )
        from_list.DeleteItem( from_index )

        # add to end of to_list
        index = to_list.GetItemCount()

        to_list.InsertStringItem( index, T_( info.label ) )
        to_list.SetItemData( index, info.col_id )
        to_list.SetStringItem( index, 1, str(info.width) )

    def OnMoveUp( self, event ):
        self.moveColumn( -1 )

    def OnMoveDown( self, event ):
        self.moveColumn( 1 )

    def moveColumn( self, direction ):
        info = self.column_info.getInfoById( self.selected_col_id )

        index = self.included_list.FindItemData( -1, info.col_id )
        name = self.included_list.GetItemText( index )

        self.included_list.DeleteItem( index )

        index += direction
        self.included_list.InsertStringItem( index, T_( info.label ) )
        self.included_list.SetItemData( index, info.col_id )
        self.included_list.SetStringItem( index, 1, str( info.width ) )
        self.included_list.SetItemState( index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED )

        # enable up and down if not at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and index != 0 )
        self.button_down.Enable( item_count > 1 and index != (item_count-1) )

    def OnWidthTextEnter( self, event ):
        info = self.column_info.getInfoById( self.selected_col_id )
        try:
            width = int(self.width_text_ctrl.GetValue())
        except ValueError:
            wx.MessageBox( T_('Width for %(name)s must be an number between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        if( width >= info.min_width
        and width <= info.max_width ):
            info.width = width
            index = self.included_list.FindItemData( -1, info.col_id )
            self.included_list.SetStringItem( index, 1, str(width) )
        else:
            wx.MessageBox( T_('Width for %(name)s must be between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )


    def OnExcludedListItemSelected( self, event ):
        self.selected_col_id = self.excluded_list.GetItemData( event.m_itemIndex )
        info = self.column_info.getInfoById( self.selected_col_id )

        self.button_up.Enable( False )
        self.button_down.Enable( False )
        self.button_include.Enable( True )
        self.button_exclude.Enable( False )

        self.width_text_ctrl.SetValue( str(info.width) )
        self.width_text_ctrl.Enable( True )

    def OnExcludedListItemDeselected( self, event ):
        self.button_include.Enable( False )
        self.width_text_ctrl.Enable( False )
        self.button_up.Enable( False )
        self.button_down.Enable( False )

    def OnIncludedListItemSelected( self, event ):
        self.selected_col_id = self.included_list.GetItemData( event.m_itemIndex )
        info = self.column_info.getInfoById( self.selected_col_id )

        self.button_exclude.Enable( info.name != 'Name' )
        self.button_include.Enable( False )

        # enable up and down if not at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and event.m_itemIndex != 0 )
        self.button_down.Enable( item_count > 1 and event.m_itemIndex != (item_count-1) )

        self.width_text_ctrl.SetValue( str(info.width) )
        self.width_text_ctrl.Enable( True )

    def OnIncludedListItemDeselected( self, event ):
        self.button_exclude.Enable( False )
        self.width_text_ctrl.Enable( False )
        self.button_up.Enable( False )
        self.button_down.Enable( False )

    def savePreferences( self ):
        p = self.app.prefs.getView()
        column_order = []
        for index in range( self.included_list.GetItemCount() ):
            col_id = self.included_list.GetItemData( index )
            column_order.append( self.column_info.getNameById( col_id ) )

        self.column_info.setColumnOrder( column_order )
        p.column_order = self.column_info.getColumnOrder()
        p.column_widths = self.column_info.getColumnWidths()

    def validate( self ):
        info = self.column_info.getInfoByName( 'Name' )
        if self.included_list.FindItemData( -1, info.col_id ) < 0:
            wx.MessageBox( T_('You must include the %s column') % (T_( info.label ),),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True
