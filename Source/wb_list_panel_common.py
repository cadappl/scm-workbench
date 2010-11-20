'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_list_panel_common.py

'''
import os
import sys
import cPickle

import wx

import wb_config
import wb_exceptions
import wb_ids
import wb_shell_commands
import wb_dialogs

class ListSortData:
    def __init__( self, order=1, field=0 ):
        self.order = order
        self.field = field

    def setField( self, field ):
        if self.field == field:
            # toggle order
            self.order *= -1
        else:
            # new field forward
            self.field = field
            self.order = 1

    def getField( self ):
        return self.field

    def getOrder( self ):
        return self.order


class ListItemState:
    def __init__( self, place_holder=False ):
        # used to tell if the state reflects a items state or is just a place holder
        self.place_holder = place_holder

        self.modified = False
        self.versioned = False
        self.new_versioned = False
        self.unversioned = False
        self.need_checkin = False
        self.need_checkout = False
        self.conflict = False
        self.file_exists = False
        self.is_folder = False
        self.is_project_parent = False
        self.revertable = False

    def printState( self, title='' ):
        print '-----------',title
        for item in self.__dict__.items():
            print 'ListState: %s -> %r' % item

class WbListCtrl(wx.ListCtrl):
    def __init__( self, parent, list_id ):
        wx.ListCtrl.__init__( self, parent, list_id,
                                style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VIRTUAL )
        self.parent = parent
        image_size = (16,16)
        il = wx.ImageList( *image_size )
        self.il_folder = il.Add( wx.ArtProvider.GetBitmap( wx.ART_FOLDER, size=image_size ) )
        self.il_file = il.Add( wx.ArtProvider.GetBitmap( wx.ART_NORMAL_FILE, size=image_size ) )
        self.AssignImageList( il, wx.IMAGE_LIST_SMALL )

    def OnGetItemText( self, item, col ):
        if self.parent.list_handler is not None:
            return self.parent.list_handler.OnGetItemText( item, col )
        else:
            return ''

    def OnGetItemImage( self, item ):
        if self.parent.list_handler is not None:
            if self.parent.list_handler.isItemImageFolder( item ):
                return self.il_folder

            else:
                return self.il_file

        return -1

    def OnGetItemAttr( self, item ):
        if self.parent.list_handler is not None:
            return self.parent.list_handler.OnGetItemAttr( item )
        else:
            return None

class WbListPanelCommon(wx.Panel):
    def __init__( self, app, frame, parent ):
        wx.Panel.__init__( self, parent )

        self.app = app
        self.frame = frame
        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        self.filter_field = T_('Name')
        self.filter_text = ''

        self.header_panel = HeaderPanel( self, app, self.filter_field )
        self.header_panel.setFilterChangedHandler( self.OnFilterChanged )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.id_list = wx.NewId()
        self.list_ctrl = WbListCtrl( self, self.id_list )

        if wb_config.focus_ring:
            self.focus_ring_panel = wx.Panel( self )

            box = wx.BoxSizer( wx.VERTICAL )
            box.Add( self.list_ctrl, 1, wx.EXPAND|wx.ALL, 3)
            self.focus_ring_panel.SetSizer( box )
            
            self.list_ctrl.Bind( wx.EVT_PAINT, self.OnPaint )

            list_window = self.focus_ring_panel
        else:
            list_window = self.list_ctrl

        self.v_sizer.Add( self.header_panel, 0, wx.EXPAND|wx.ALL, 0 )
        self.v_sizer.Add( list_window, 1, wx.EXPAND|wx.ALL, 0 )

        acc_tab = wx.AcceleratorTable( self.getAcceleratorTableInit() )
        self.list_ctrl.SetAcceleratorTable( acc_tab )

        wx.EVT_SIZE( self, try_wrapper( self.OnSize ) )

        wx.EVT_LIST_COL_CLICK( self.list_ctrl, self.id_list, self.app.eventWrapper( self.OnColClick ))

        wx.EVT_LIST_ITEM_ACTIVATED( self.list_ctrl, self.id_list, self.app.eventWrapper( self.OnItemActivated ) )

        wx.EVT_LIST_ITEM_RIGHT_CLICK( self.list_ctrl, self.id_list, self.app.eventWrapper( self.OnRightClick ) )
        if wx.Platform in ['__WXMSW__','__WXMAC__']:
            wx.EVT_LIST_BEGIN_DRAG( self.list_ctrl, self.id_list, self.app.eventWrapper( self.OnDragBegin ) )

        wx.EVT_LIST_ITEM_SELECTED( self.list_ctrl, self.id_list, self.OnItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self.list_ctrl, self.id_list, self.OnItemDeselected )

        wx.EVT_SET_FOCUS( self.list_ctrl, self.OnSetFocus )
        wx.EVT_KILL_FOCUS( self.list_ctrl, self.OnKillFocus )  

        self.addToSizer( self.v_sizer )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        view_prefs = self.app.prefs.getView()
        self.sort_data = ListSortData( view_prefs.sort_order, view_prefs.sort_field )

        self.list_handler = None

        self.last_char_timestamp = 0
        self.inc_search_string = ''

        self.__first_time_select_allowed = True

    def firstTimeSelect( self ):
        if self.__first_time_select_allowed:
            if self.list_handler is not None:
                if len( self.list_handler.all_files ) > 0:
                    wx.CallAfter( self.list_ctrl.Select, 0 )
        self.__first_time_select_allowed = False

    def __repr__( self ):
        return '<WbListPanelCommon %r>' % self.list_handler

    def OnPaint( self, event ):
        event.Skip()
        return

        dc = wx.PaintDC( self )
        #dc.Clear()
        w, h = self.GetSize()
        if self.FindFocus() == self.list_ctrl:
            print 'list focus'
            dc.SetPen( wx.Pen( "red", 1 ) )
            dc.DrawRectangle( 0, 0, w, h )
        else:
            dc.SetPen( wx.Pen( "green", 1 ) )
            dc.DrawRectangle( 0, 0, w, h )
            print 'list unfocus'

        event.Skip()

    def addToSizer( self, v_sizer ):
        pass

    def setFocusFilter( self ):
        self.header_panel.setFocusFilter()

    def OnSetFocus( self, event ):
        #self.frame.setEventHandler( self )

        if wb_config.focus_ring:
            self.Refresh()

        event.Skip()

    def OnKillFocus( self, event ):
        #self.frame.clearEventHandler()

        if wb_config.focus_ring:
            self.Refresh()

        event.Skip()

    def OnItemSelected( self, event ):
        self.frame.clearUpdateUiState()
        self.frame.setEventHandler( self )

    def OnItemDeselected( self, event ):
        self.frame.clearUpdateUiState()
        self.frame.setEventHandler( self )

    def OnDragBegin( self, event ):
        #print 'WbListPanel.OnDragBegin'

        all_filenames = [self.list_handler.getFilename( row ) for row in self.getSelectedRows()]

        # create our own data format and use it in a
        # custom data object
        svn_data = wx.CustomDataObject(wx.CustomDataFormat("WorkBench.svn_wc_path"))
        svn_data.SetData( cPickle.dumps( all_filenames ) )

        # Make a data object that other apps will recognize as a filename drag/drop
        fn_data = wx.FileDataObject()
        for name in all_filenames:
            fn_data.AddFile(name)

# What is this for?  It just screws up the dragging of files to a text editor
# that also accepts files...
#        # Now make a data object for the text and also a composite
#        # data object holding both of the others.
#        text_data = wx.TextDataObject( 'the text of the list ctrl file name' )

        data = wx.DataObjectComposite()
        data.Add( svn_data )
#        data.Add( text_data )
        data.Add( fn_data )

        # And finally, create the drop source and begin the drag
        # and drop opperation
        src = wx.DropSource( self )
        src.SetData( data )
        #print 'Begining DragDrop'
        src.DoDragDrop( wx.Drag_AllowMove )
        #print 'DragDrop completed: %d' % result

    def savePreferences( self ):
        view_prefs = self.app.prefs.getView()
        view_prefs.sort_order = self.sort_data.getOrder()
        view_prefs.sort_field = self.sort_data.getField()

    def getProjectInfo( self ):
        if self.list_handler is not None:
            return self.list_handler.getProjectInfo()
        return None

    def clearHandler( self ):
        self.app.log.debug( 'WbListPanelCommon.clearHandler()' )
        self.list_handler = None
        # empty the list
        self.list_ctrl.DeleteAllItems()

    def updateHandler( self ):
        self.app.log.debug( 'WbListPanelCommon.updateHandler() %r' % self.list_handler )
        if self.list_handler is not None:
            self.list_handler.setupColumns()
            self.list_handler.updateStatus()

        self.drawList()

    def setHandler( self, list_handler ):
        self.app.log.debug( 'WbListPanelCommon.setHandler( %r )' % list_handler )
        self.list_handler = list_handler
        self.list_handler.setupColumns()
        self.list_handler.updateStatus()

        self.list_ctrl.SetBackgroundColour( self.list_handler.getBackgroundColour() )

        self.filter_field = ''
        self.header_panel.clearFilterText()

        self.drawList()

    def drawList( self ):
        self.app.log.debug( 'WbListPanelCommon.drawList() %r' % self.list_handler )

        if self.list_handler:
            self.list_handler.initList( self.sort_data, self.filter_field, self.filter_text )

    def getHandler( self ):
        return self.list_handler

    def updateHeader( self, url_name, path_name ):
        self.header_panel.updateHeader( url_name, path_name )

    def OnFilterChanged( self, field, text ):
        self.filter_field = field
        self.filter_text = text
        self.drawList()

    def OnSize( self, event ):
        w, h = self.GetClientSizeTuple()
        self.v_sizer.SetDimension( 0, 0, w, h )

    def OnItemActivated(self, event):
        if not self.list_handler:
            return

        # ignore the specified prompts
        if self.list_handler.project_info.need_checkout:
            return

        for row in self.getSelectedRows():
            filename = self.list_handler.getFilename( row )
            if self.list_handler.mayOpen( row ):
                self.app.selectTreeNode( filename )

            elif not os.path.isdir( filename ):
                wb_shell_commands.EditFile( self.app, self.list_handler.getProjectInfo(), filename )

    def isTreeHandler( self ):
        return False

    def isListHandler( self ):
        return True

    def getUpdateUiState( self ):
        if self.list_handler is None:
            return None
        return self.list_handler.getState( self.getSelectedRows() )

    def OnRightClick( self, event ):
        if not self.list_handler:
            return

        self.frame.getUpdateUiState()
        if True:
            menu = self.list_handler.getContextMenu()
            self.list_ctrl.PopupMenu( menu, event.GetPoint() )
            menu.Destroy()

    def OnColClick( self, event ):
        self.app.log.debug( 'OnColClick %r' % self.list_handler  )
        self.sort_data.setField( self.list_handler.getColumnId( event.m_col ) )
        if not self.list_handler:
            return

        self.list_handler.sortList( self.sort_data )


    # command handlers
    def OnFileEdit( self ):
        if not self.list_handler:
            return

        for row in self.getSelectedRows():
            filename = self.list_handler.getFilename( row )

            wb_shell_commands.EditFile( self.app, self.list_handler.getProjectInfo(), filename )

    def OnShellOpen( self ):
        if not self.list_handler:
            return

        for row in self.getSelectedRows():
            filename = self.list_handler.getFilename( row )

            wb_shell_commands.ShellOpen( self.app, self.list_handler.getProjectInfo(), filename )

    def OnSpEditCopy( self ):
        return self.Sp_Dispatch( 'Cmd_File_EditCopy' )

    def OnSpEditCut( self ):
        return self.Sp_Dispatch( 'Cmd_File_EditCut' )

    def OnSpEditPaste( self ):
        return self.Sp_Dispatch( 'Cmd_File_EditPaste' )

    def OnSpAdd( self ):
        return self.Sp_Dispatch( 'Cmd_File_Add' )

    def OnSpAnnotate( self ):
        return self.Sp_Dispatch( 'Cmd_File_Annotate' )

    def OnSpCheckin( self ):
        return self.Sp_Dispatch( 'Cmd_File_Checkin' )

    def OnSpCleanup( self ):
        return self.Sp_Dispatch( 'Cmd_File_Cleanup' )

    def OnSpDelete( self ):
        return self.Sp_Dispatch( 'Cmd_File_Delete' )

    def OnSpDiffWorkBase( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffWorkBase' )

    def OnSpDiffWorkHead( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffWorkHead' )
 
    def OnSpDiffWorkBranchOriginBase( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffWorkBranchOriginBase' )
 
    def OnSpDiffWorkBranchOriginHead( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffWorkBranchOriginHead' )

    def OnSpDiffMineNew( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffMineNew' )

    def OnSpDiffOldMine( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffOldMine' )

    def OnSpDiffOldNew( self ):
        return self.Sp_Dispatch( 'Cmd_File_DiffOldNew' )

    def OnSpHistory( self ):
        return self.Sp_Dispatch( 'Cmd_File_History' )

    def OnSpInfo( self ):
        return self.Sp_Dispatch( 'Cmd_File_Info' )

    def OnSpLock( self ):
        return self.Sp_Dispatch( 'Cmd_File_Lock' )

    def OnSpProperties( self ):
        return self.Sp_Dispatch( 'Cmd_File_Properties' )

    def OnSpRename( self ):
        return self.Sp_Dispatch( 'Cmd_File_Rename' )

    def OnSpRevert( self ):
        return self.Sp_Dispatch( 'Cmd_File_Revert' )

    def OnSpResolved( self ):
        return self.Sp_Dispatch( 'Cmd_File_Resolved' )

    def OnSpUnlock( self ):
        return self.Sp_Dispatch( 'Cmd_File_Unlock' )

    def OnSpUpdate( self ):
        return self.Sp_Dispatch( 'Cmd_File_Update' )

    def OnSpUpdateTo( self ):
        return self.Sp_Dispatch( 'Cmd_File_UpdateTo' )

    def Sp_Dispatch( self, sp_func_name ):
        self.app.trace.info( 'WbListPanel.Sp_Dispatch( %s ) event' % sp_func_name )
        if not self.list_handler:
            return

        sp_func = getattr( self.list_handler, sp_func_name )

        self.app.trace.info( 'WbListPanel.Sp_Dispatch( %s ) calling' % sp_func_name )
        return sp_func( self.getSelectedRows() )

    def selectAll( self ):
        item_index = -1
        while True:
            item_index = self.list_ctrl.GetNextItem( item_index, wx.LIST_NEXT_ALL )
            if item_index < 0:
                break

            focused = self.list_ctrl.GetItemState( item_index, wx.LIST_STATE_FOCUSED )
            self.list_ctrl.SetItemState( item_index, wx.LIST_STATE_SELECTED | focused, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED )

    def getSelectedRows( self ):
        all_rows = []
        item_index = -1
        while True:
            item_index = self.list_ctrl.GetNextItem( item_index, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED )
            if item_index < 0:
                break

            all_rows.append( item_index )

        all_rows.sort()

        #print 'getSelectedRows() %r' % all_rows
        return all_rows
        
class HeaderPanel(wx.Panel):
    def __init__( self, parent, app, filter_field ):
        wx.Panel.__init__(self, parent, -1)

        self.app = app

        self.background_colour = wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DFACE )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer1 = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer2 = wx.BoxSizer( wx.HORIZONTAL )

        # Don't set the controls readonly as that prevents copy of the text
        self.url_text_ctrl = wx.TextCtrl( self, 0, '' )
        self.path_text_ctrl = wx.TextCtrl( self, 0, '' )

        self.filter_changed_handler = None

        # ToDo:  A wx.SearchCtrl would go great here instead of these widgets
        self.filter_field_choices = [ T_('Name'), T_('Author') ]
        self.filter_choice_ctrl = wx.Choice( self, wx.NewId(), choices=self.filter_field_choices )
        self.filter_choice_ctrl.SetSelection( self.filter_field_choices.index( filter_field ) )
        self.filter_text_ctrl = wx.TextCtrl( self )
        self.filter_clear_button = wx.Button( self, wx.NewId(), 'X', style=wx.BU_EXACTFIT, size=(30, -1) )

        # share the space 50/50
        if 'wxMac' in wx.PlatformInfo:
            filter_flags = wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
            border = 5
            left = wx.LEFT
        else:
            filter_flags = wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
            border = 3
            left = 0
        self.h_sizer1.Add( self.url_text_ctrl, 1,  left|wx.TOP|wx.BOTTOM|wx.RIGHT, border )
        self.h_sizer1.Add( self.path_text_ctrl, 1, wx.TOP|wx.BOTTOM|wx.RIGHT, border )

        self.h_sizer2.Add( self.filter_choice_ctrl, 0,  left|filter_flags, border )
        self.h_sizer2.Add( self.filter_text_ctrl, 1,    filter_flags, border )
        self.h_sizer2.Add( self.filter_clear_button, 0, filter_flags, border )

        self.v_sizer.Add( self.h_sizer1, 0, wx.EXPAND|wx.ALL, 0 )
        self.v_sizer.Add( self.h_sizer2, 1, wx.EXPAND|wx.ALL, 0 )

        wx.EVT_BUTTON( self, self.filter_clear_button.GetId(), self.OnClearFilterText )
        wx.EVT_TEXT( self, self.filter_text_ctrl.GetId(), self.OnFilterTextChanged )
        wx.EVT_CHOICE( self, self.filter_choice_ctrl.GetId(), self.OnFilterTypeChanged )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()


    def setFocusFilter( self ):
        self.filter_text_ctrl.SetFocus()

    def setFilterChangedHandler( self, handler ):
        self.filter_changed_handler = handler

    def __callFilterChangedHandler( self ):
        self.filter_changed_handler(
            self.filter_field_choices[ self.filter_choice_ctrl.GetSelection() ],
            self.filter_text_ctrl.GetValue() )

    def updateHeader(self, url_name, path_name ):
        if url_name is None:
            url_name = ''
        if path_name is None:
            path_name = ''

        self.url_text_ctrl.SetValue( url_name )
        self.path_text_ctrl.SetValue( path_name )

        self.SetBackgroundColour( self.background_colour )
        self.Refresh()

    def clearFilterText( self ):
        self.filter_text_ctrl.Clear()
        self.__callFilterChangedHandler()

    def OnClearFilterText( self, event=None ):
        self.filter_text_ctrl.Clear()
        self.__callFilterChangedHandler()

    def OnFilterTypeChanged( self, event ):
        self.filter_text_ctrl.Clear()
        self.__callFilterChangedHandler()

    def OnFilterTextChanged( self, event ):
        self.__callFilterChangedHandler()

class ListHandler:
    def __init__( self, list_panel ):
        self.list_panel = list_panel

    def sortList( self, sort_data ):
        raise wb_exceptions.InternalError( 'sortList not implemented' )
