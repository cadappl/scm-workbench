'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_tree_panel.py

'''
import wx
import cPickle
import os
import pysvn

import wb_exceptions
import wb_source_control_providers
import wb_ids
import wb_shell_commands
import wb_dialogs
import wb_project_dialogs

import wb_config
import wb_torun_configspec

class TreeState:
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
        self.is_folder = True
        self.is_project_parent = False
        self.revertable = False

    def printState( self, title='' ):
        print '--------', title
        for item in self.__dict__.items():
            print 'TreeState: %s -> %r' % item


#--------------------------------------------------------------------------------
#
#
#    WbTreePanel
#
#
#--------------------------------------------------------------------------------
class WbTreePanel(wx.Panel):
    ''' WbTreePanel '''

    last_position_bookmark_name = 'last position'

    def __init__( self, app, frame, parent ):
        self.app = app
        self.frame = frame
        self.list_panel = frame.list_panel
        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        wx.Panel.__init__( self, parent )

        self.tree_ctrl = WbTreeCtrl( self, self.app )

        if wb_config.focus_ring:
            box = wx.BoxSizer()
            box.Add( self.tree_ctrl, 1, wx.EXPAND|wx.ALL, 3)
            self.SetSizer( box )

            self.tree_ctrl.Bind( wx.EVT_PAINT, self.OnPaint )

        acc_init = [
                (wx.ACCEL_CMD, ord('C'), wb_ids.id_SP_EditCopy),
                (wx.ACCEL_CMD, ord('X'), wb_ids.id_SP_EditCut),
                (wx.ACCEL_CMD, ord('V'), wb_ids.id_SP_EditPaste),

                (wx.ACCEL_CMD, ord('A'), wb_ids.id_SP_Add),
                (wx.ACCEL_CMD, ord('L'), wb_ids.id_SP_History),
                (wx.ACCEL_CMD, ord('I'), wb_ids.id_SP_Info),
                (wx.ACCEL_CMD, ord('P'), wb_ids.id_SP_Properties),
                (wx.ACCEL_CMD, ord('R'), wb_ids.id_SP_Revert),
                (wx.ACCEL_CMD, ord('T'), wb_ids.id_SP_UpdateTo),
                (wx.ACCEL_CMD, ord('U'), wb_ids.id_SP_Update),
                (wx.ACCEL_NORMAL, wx.WXK_DELETE, wb_ids.id_SP_Delete),
                (wx.ACCEL_CMD, ord('O'), wb_ids.id_Shell_Open),
                ]

        acc_tab = wx.AcceleratorTable( acc_init )
        self.tree_ctrl.SetAcceleratorTable( acc_tab )

        self.tree_drop_target = SvnDropTarget( self )
        self.tree_ctrl.SetDropTarget( self.tree_drop_target )

        wx.EVT_SIZE( self, try_wrapper( self.OnSize ) )
        wx.EVT_TREE_ITEM_EXPANDING( self, self.tree_ctrl.getId(), try_wrapper( self.OnItemExpanding ) )
        wx.EVT_TREE_SEL_CHANGED( self, self.tree_ctrl.GetId(), try_wrapper( self.OnTreeSelChanged ) )
        wx.EVT_LEFT_DOWN( self.tree_ctrl, try_wrapper( self.OnLeftDown ) )
        wx.EVT_RIGHT_DOWN( self.tree_ctrl, try_wrapper( self.OnRightDown ) )
        wx.EVT_RIGHT_UP( self.tree_ctrl, try_wrapper( self.OnRightUp ) )

        wx.EVT_MENU( self, wb_ids.id_Project_Add, try_wrapper( self.OnProjectAdd ) )
        wx.EVT_MENU( self, wb_ids.id_Project_Delete, try_wrapper( self.OnProjectDelete ) )
        wx.EVT_MENU( self, wb_ids.id_Project_Update, try_wrapper( self.OnProjectUpdate ) )

        if wx.Platform in ['__WXMSW__', '__WXMAC__']:
            wx.EVT_TREE_BEGIN_DRAG( self.tree_ctrl, self.tree_ctrl.GetId(), self.app.eventWrapper( self.OnDragBegin ) )
            wx.EVT_TREE_END_DRAG( self.tree_ctrl, self.tree_ctrl.GetId(), self.app.eventWrapper( self.OnDragEnd ) )

        wx.EVT_SET_FOCUS( self.tree_ctrl, self.OnSetFocus )
        wx.EVT_KILL_FOCUS( self.tree_ctrl, self.OnKillFocus )

        # start up by skipping ui updates until we have the tree control initialised
        self.__skip_update_ui = True

    def __repr__( self ):
        return '<WbTreePanel %r>' % self.getSelectionProjectInfo()

    def OnPaint( self, event ):
        dc = wx.PaintDC( self )
        dc.Clear()
        w, h = self.GetSize()
        if self.FindFocus() == self.tree_ctrl:
            print 'tree focus'
            dc.SetPen( wx.Pen( "red", 1 ) )
            dc.DrawRectangle( 0, 0, w, h )
        else:
            dc.SetPen( wx.Pen( "green", 1 ) )
            dc.DrawRectangle( 0, 0, w, h )
            print 'tree unfocus'
        event.Skip()

    def initFrame( self ):
        bookmark_pi = None

        project_list = self.app.prefs.getProjects().getProjectList()

        if( self.app.auto_project_dir is not None
        and wb_source_control_providers.hasProvider( 'subversion' ) ):
            provider = wb_source_control_providers.getProvider( 'subversion' )
            cmd_project_info = provider.getProjectInfo( self.app )
            project_name = os.path.basename( self.app.auto_project_dir )

            try:
                url = pysvn.Client().info( self.app.auto_project_dir ).url

                cmd_project_info.init( project_name, url = url, wc_path = self.app.auto_project_dir )

                for project in project_list:
                    if project.isChild( cmd_project_info ):
                        bookmark_pi = cmd_project_info
                        break
                else:
                    self.app.prefs.getProjects().addProject( cmd_project_info )
                    project_list = self.app.prefs.getProjects().getProjectList()

                    bookmark_pi = cmd_project_info

            except pysvn.ClientError:
                pass

        self.initTree( project_list )

        if bookmark_pi is not None:
            self.gotoProjectInfo( bookmark_pi )
        else:
            self.gotoBookmark( self.last_position_bookmark_name )

        self.list_panel.firstTimeSelect()

    def OnSetFocus( self, event ):
        if wb_config.debug_selection: print 'ZT: WbTreePanel OnSetFocus'
        self.frame.setEventHandler( self )

        if wb_config.focus_ring:
            self.Refresh()

        event.Skip()

    def OnKillFocus( self, event ):
        if wb_config.debug_selection: print 'ZT: WbTreePanel OnKillFocus'
        #self.frame.clearEventHandler()

        if wb_config.focus_ring:
            self.Refresh()

        event.Skip()

    def OnDragBegin( self, event ):
        #print 'WbTreePanel.OnDragBegin'
        pass

    def OnDragEnd( self, event ):
        #print 'WbTreePanel.OnDragEnd'
        pass

    def getSelectionProjectHandler( self ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return None

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        return handler

    def getSelectionProjectInfo( self ):
        handler = self.getSelectionProjectHandler()
        if not handler:
            return None

        return handler.getProjectInfo()

    def getProjectTopProjectInfo( self ):
        item = self.tree_ctrl.GetSelection()

        while item:
            handler = self.tree_ctrl.GetPyData( item )
            if handler.isProjectParent():
                return handler.getProjectInfo()
            item = self.tree_ctrl.GetItemParent( item )

        return None

    def savePreferences( self ):
        bm_prefs = self.app.prefs.getBookmarks()
        if bm_prefs.hasBookmark( self.last_position_bookmark_name ):
            bm_prefs.delBookmark( self.last_position_bookmark_name )

        tree_pi = self.getSelectionProjectInfo()
        if tree_pi is not None:
            bm_prefs.addBookmark( tree_pi, name=self.last_position_bookmark_name )

    def initTree( self, project_info_list ):
        self.__skip_update_ui = True

        self.root_item = self.tree_ctrl.AddRoot( T_("Projects:") )
        self.tree_ctrl.SetPyData( self.root_item, RootTreeItem() )
        first_item = None
        for project_info in project_info_list:
            provider = wb_source_control_providers.getProvider( project_info.provider_name )

            item = self.tree_ctrl.AppendItem( self.root_item, project_info.project_name )
            if first_item is None:
                first_item = item

            # mark all the project parents as such
            handler = provider.getProjectTreeItem( self.app, project_info )
            handler.setIsProjectParent()

            self.tree_ctrl.SetPyData( item, handler )
            self.tree_ctrl.SetItemHasChildren( item, handler.mayExpand() )
            self.tree_ctrl.SetItemTextColour( item, handler.getTreeNodeColour() )

        self.tree_ctrl.SortChildren( self.root_item )
        #self.tree_ctrl.Expand( self.root_item )

        self.__skip_update_ui = False

        if first_item:
            self.tree_ctrl.SelectItem( first_item )
            self.tree_ctrl.EnsureVisible( first_item )

    def updateTreeSelectedItem( self ):
        self.updateTreeItem( self.tree_ctrl.GetSelection() )

    def updateTreeItem( self, this_item ):
        if this_item is None:
            return

        handler = self.tree_ctrl.GetPyData( this_item )
        self.tree_ctrl.SetItemTextColour( this_item, handler.getTreeNodeColour() )
        pi = handler.getProjectInfo()
        if not pi:
            return

        project_info_list = handler.getExpansion()
        # remove any items that are no longer present
        del_items = []
        found_pi = []

        child_item, cookie = self.tree_ctrl.GetFirstChild( this_item )
        while child_item:
            tree_pi = self.tree_ctrl.GetPyData( child_item ).getProjectInfo()

            found = False
            for index, pi in enumerate( project_info_list ):
                if tree_pi.isEqual( pi ):
                    found = True
                    found_pi.append( index )
                    break
            if not found:
                del_items.append( child_item )

            child_item, cookie = self.tree_ctrl.GetNextChild( this_item, cookie )

        for child_item in del_items:
            self.tree_ctrl.Delete( child_item )

        for index, project_info in enumerate( project_info_list ):
            if index not in found_pi:
                provider = wb_source_control_providers.getProvider( project_info.provider_name )

                child_item = self.tree_ctrl.AppendItem( this_item, project_info.project_name )
                child_handler = provider.getProjectTreeItem( self.app, project_info )
                self.tree_ctrl.SetPyData( child_item, child_handler )
                self.tree_ctrl.SetItemTextColour( child_item, wb_config.colour_status_qqq )

        self.tree_ctrl.SortChildren( this_item )

        child_item, cookie = self.tree_ctrl.GetFirstChild( this_item )
        while child_item:
            child_handler = self.tree_ctrl.GetPyData( child_item )
            self.tree_ctrl.SetItemHasChildren( child_item, child_handler.mayExpand() )
            self.tree_ctrl.SetItemTextColour( child_item, child_handler.getTreeNodeColour() )

            child_item, cookie = self.tree_ctrl.GetNextChild( this_item, cookie )

        # set the has children state
        self.tree_ctrl.SetItemHasChildren( this_item, len(project_info_list) > 0 )

    def gotoBookmark( self, bookmark_name ):
        bm = self.app.prefs.getBookmarks()
        if not bm.hasBookmark( bookmark_name ):
            return

        pi = bm.getBookmark( bookmark_name )
        self.gotoProjectInfo( pi )

    def gotoProjectInfo( self, pi ):
        parent_item = self.tree_ctrl.GetRootItem()

        child_item, cookie = self.tree_ctrl.GetFirstChild( parent_item )
        while child_item:
            tree_pi = self.tree_ctrl.GetPyData( child_item ).getProjectInfo()
            if tree_pi.isEqual( pi ):
                # found it
                break

            if tree_pi.isChild( pi ):
                # drill deeper
                self.tree_ctrl.Expand( child_item )
                # child becomes parent at next level
                parent_item = child_item
                child_item, cookie = self.tree_ctrl.GetFirstChild( parent_item )
            else:
                # keep looking at this level
                child_item, cookie = self.tree_ctrl.GetNextChild( parent_item, cookie )

        if child_item:
            self.tree_ctrl.SelectItem( child_item )
            self.tree_ctrl.EnsureVisible( child_item )

    def getItemHandler( self, event ):
        item = event.GetItem()
        if not item:
            return None
        handler = self.tree_ctrl.GetPyData( item )
        return handler

    def updateTree( self, item=None ):
        if not item:
            item = self.tree_ctrl.GetRootItem()

        child_item, cookie = self.tree_ctrl.GetFirstChild( item )
        while child_item:
            handler = self.tree_ctrl.GetPyData( child_item )
            if handler.mayExpand():
                self.tree_ctrl.SetItemHasChildren( child_item )
            else:
                self.tree_ctrl.DeleteChildren( child_item )
                self.tree_ctrl.SetItemHasChildren( child_item, False )

            self.updateTree( child_item )

            child_item, cookie = self.tree_ctrl.GetNextChild( child_item, cookie )


    def OnActivateApp( self, is_active ):
        # pass to tree and let it pass to list
        self.list_panel.OnActivateApp( is_active )

    def refreshTree( self ):
        # need to restore the tree event handler if its currently active
        set_tree_handler = self.frame.isEventHandler( self )
        self.app.log.debug( 'refreshTree set_tree_handler %r' % set_tree_handler )

        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        handler = self.tree_ctrl.GetPyData( item )
        tree_pi = handler.getProjectInfo()
        if not tree_pi:
            return

        p = self.app.prefs.getView()
        if p.view_recursive:
            busy = wx.BusyInfo( T_("Refreshing view..."), self.frame )
        tree_pi.updateStatus()
        self.updateTreeItem( item )

        self.list_panel.drawList()

        if set_tree_handler:
            # restore handler
            self.frame.setEventHandler( self )

    def expandSelectedTreeNode( self ):
        self.refreshTree()
        item = self.tree_ctrl.GetSelection()
        if item:
            self.tree_ctrl.Expand( item )

    def selectTreeNodeInParent( self, filename ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return
        self.tree_ctrl.SelectItem( self.tree_ctrl.GetItemParent( item ) )
        self.selectTreeNode( filename )
        
    def selectTreeNode( self, filename ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        name = os.path.basename( filename )
        sub_item = self.tree_ctrl.getItemByName( item, name )
        if sub_item:
            self.tree_ctrl.SelectItem( sub_item )


    #---------- Event handlers ----------------------------------------------
    def OnSize( self, event ):
        w, h = self.GetClientSizeTuple()
        self.tree_ctrl.SetDimensions( 0, 0, w, h )

    # Handler for when a new selection is made in the tree control child
    def OnTreeSelChanged( self, event ):
        if wb_config.debug_selection: print 'ZT: WbTreePanel OnTreeSelChanged __skip_update_ui', self.__skip_update_ui
        if self.__skip_update_ui:
            return

        tree_item = self.getItemHandler( event )
        self.changedSelection( tree_item )

    def changedSelection( self, tree_item ):
        if wb_config.debug_selection: print 'ZT: WbTreePanel changedSelection'
        self.frame.clearUpdateUiState()
        self.frame.setEventHandler( self )

        # Update the contents of the list control to reflect the new selection
        if not tree_item:
            return

        pi = tree_item.getProjectInfo()

        # see if already handling this project
        if pi == self.list_panel.getProjectInfo():
            return;

        p = self.app.prefs.getView()
        if p.view_recursive:
            busy = wx.BusyInfo( T_("Refreshing view..."), self.frame )
        if pi is None:
            self.list_panel.clearHandler()
        else:
            provider = wb_source_control_providers.getProvider( pi.provider_name )

            list_handler = provider.getListHandler( self.app, self.list_panel, tree_item.getProjectInfo() )

            # if this tree item is a project parent then set the list panel as one
            if tree_item.isProjectParent():
                list_handler.setIsProjectParent()

            # draw the list - its updates the status info
            self.list_panel.setHandler( list_handler )
            # fix up the tree if required
            self.updateTreeItem( self.tree_ctrl.GetSelection() )

    def OnItemExpanding( self, event ):
        this_item = event.GetItem()

        item = self.tree_ctrl.GetSelection()
        if this_item is item:
            return

        if not self.tree_ctrl.ItemHasChildren( this_item ):
            return

        if self.tree_ctrl.GetChildrenCount( this_item, False ) != 0:
            return

        handler = self.getItemHandler( event )
        if not handler:
            return

        handler.getProjectInfo().updateStatus()
        self.updateTreeItem( this_item )

    def isTreeHandler( self ):
        return True

    def isListHandler( self ):
        return False

    def getUpdateUiState( self ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return None

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        return handler.getState()

    def OnLeftDown( self, event ):
        if wb_config.debug_selection: print 'OnLeftDown',
        item = self.tree_ctrl.GetSelection()
        if not item:
            if wb_config.debug_selection: print 'no item selected'
            return

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            if wb_config.debug_selection: print 'no handler'
            return
        if wb_config.debug_selection: print 'handler %r' % handler
        event.Skip()

    def OnRightDown( self, event ):
        # move the selection to the clicked on node
        point = event.GetPosition();
        item, flags = self.tree_ctrl.HitTest( point )
        if (flags&wx.TREE_HITTEST_NOWHERE) != 0:
            return
        self.tree_ctrl.SelectItem( item )
        self.changedSelection( self.tree_ctrl.GetPyData( item ) )

        if wx.Platform == '__WXMAC__':
            self.popUpContextMenu( item, point )

    def OnRightUp( self, event ):
        # move the selection to the clicked on node
        point = event.GetPosition();
        item, flags = self.tree_ctrl.HitTest( point )
        if not item:
            return

        self.tree_ctrl.SelectItem( item )
        self.changedSelection( self.tree_ctrl.GetPyData( item ) )

        if wx.Platform != '__WXMAC__':
            self.popUpContextMenu( item, point )

    def popUpContextMenu( self, item, point ):
        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        self.frame.getUpdateUiState()

        menu = handler.getContextMenu( self.frame.ui_state_tree )
        if handler.isProjectParent():
            menu.AppendSeparator()
            menu.Append( wb_ids.id_Project_Update, T_('Project Settings') )
            menu.Append( wb_ids.id_Project_Delete, T_('Delete Project') )

        self.tree_ctrl.PopupMenu( menu, point )
        menu.Destroy()

    def OnProjectAdd( self, event ):
        dialog = wb_project_dialogs.AddProjectDialog( self.app, self )
        rc = dialog.ShowModal()
        if rc == wx.ID_OK:
            project_info = dialog.getProjectInfo()
            self.app.prefs.getProjects().addProject( project_info )
            self.app.savePreferences()

            provider = wb_source_control_providers.getProvider( project_info.provider_name )

            item = self.tree_ctrl.AppendItem( self.root_item, project_info.project_name )

            # mark all the project parents as such
            handler = provider.getProjectTreeItem( self.app, project_info )
            handler.setIsProjectParent()

            self.tree_ctrl.SetPyData( item, handler )
            if handler.mayExpand():
                self.tree_ctrl.SetItemHasChildren( item )
            else:
                self.tree_ctrl.SetItemHasChildren( item, False )

            self.tree_ctrl.SortChildren( item )
            self.tree_ctrl.SelectItem( item )
            self.tree_ctrl.EnsureVisible( item )

    def OnProjectDelete( self, event ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        handler = self.tree_ctrl.GetPyData( item )
        tree_pi = handler.getProjectInfo()
        if not tree_pi:
            return

        dialog = wb_dialogs.ConfirmAction( self, T_('Delete Project'),
                [('', tree_pi.project_name)] )

        rc = dialog.ShowModal()
        if rc == wx.ID_OK:
            # get rid of the old
            self.app.prefs.getProjects().delProject( tree_pi )
            self.app.savePreferences()

            self.tree_ctrl.Delete( item )
            
            # back to the top
            self.tree_ctrl.SelectItem( self.root_item )

    def OnProjectUpdate( self, event ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        handler = self.tree_ctrl.GetPyData( item )
        tree_pi = handler.getProjectInfo()
        if not tree_pi:
            return

        provider = wb_source_control_providers.getProvider( tree_pi.provider_name )
        dialog = provider.getUpdateProjectDialog( self.app, self, tree_pi )
        rc = dialog.ShowModal()
        if rc == wx.ID_OK:
            # get rid of the old
            self.app.prefs.getProjects().delProject( tree_pi )
            self.tree_ctrl.Delete( item )

            # just like the add code
            project_info = dialog.getProjectInfo()
            self.app.prefs.getProjects().addProject( project_info )
            self.app.savePreferences()

            provider = wb_source_control_providers.getProvider( project_info.provider_name )

            item = self.tree_ctrl.AppendItem( self.root_item, project_info.project_name )

            # mark all the project parents as such
            handler = provider.getProjectTreeItem( self.app, project_info )
            handler.setIsProjectParent()

            self.tree_ctrl.SetPyData( item, handler )
            if handler.mayExpand():
                self.tree_ctrl.SetItemHasChildren( item )
            else:
                self.tree_ctrl.SetItemHasChildren( item, False )

            self.tree_ctrl.SortChildren( self.root_item )
            self.tree_ctrl.SelectItem( item )

    # command handlers
    def OnCommandShell( self ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return

        wb_shell_commands.CommandShell( self.app, handler.getProjectInfo() )

    def OnFileBrowser( self ):
        item = self.tree_ctrl.GetSelection()
        if not item:
            return

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return

        wb_shell_commands.FileBrowser( self.app, handler.getProjectInfo() )

    def OnSpCreateBranch( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_CreateBranch' )

    def OnSpCreateTag( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_CreateTag' )

    def OnSpEditCopy( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_EditCopy' )

    def OnSpEditCut( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_EditCut' )

    def OnSpEditPaste( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_EditPaste' )


    def OnSpAdd( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Add' )

    def OnSpCleanup( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Cleanup' )

    def OnSpCheckin( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Checkin' )

    def OnSpCheckout( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Checkout' )

    def OnSpCheckoutTo( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_CheckoutTo' )

    def OnSpDelete( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Delete' )

    def OnSpDiffWorkBase( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_DiffWorkBase' )

    def OnSpDiffWorkHead( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_DiffWorkHead' )
 
    def OnSpHistory( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_History' )

    def OnSpInfo( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Info' )

    def OnSpMkdir( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Mkdir' )

    def OnSpNewFile( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_NewFile' )

    def OnSpProperties( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Properties' )

    def OnSpRename( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Rename' )

    def OnReportUpdates( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_ReportUpdates' )

    def OnReportLocksWc( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_ReportLocksWc' )

    def OnReportLocksRepos( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_ReportLocksRepos' )

    def OnReportBranchChanges( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_ReportBranchChanges' )

    def OnSpRevert( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Revert' )

    def OnSpUpdate( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Update' )

    def OnSpUpdateTo( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_UpdateTo' )

    def OnSpSwitch( self ):
        return self.Sp_Dispatch( 'Cmd_Dir_Switch' )

    def Sp_DispatchEvent( self, event ):
        self.app.trace.info( 'WbTreePanel.Sp_DispatchEvent( %r ) event' % event )
        item = self.tree_ctrl.GetSelection()
        if not item:
            return None

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        project_info = getattr( handler, 'project_info' )
        if not project_info:
            return

        menu_info = project_info.menu_info
        if not menu_info:
            return

        for id, func, fn in menu_info:
            if id == event.GetId():
                self.app.trace.info( 'WbTreePanel.Sp_Torun_Dispatch( %r ) calling' % fn )

                if fn is None:
                    print 'Not implemented for' % id
                    return None
                else:
                    return fn( handler.getProjectInfo() )

        return None

    #----------------------------------------
    def OnSpCopy( self, filename_list ):
        return self.Sp_DispatchDrop( 'Cmd_Dir_Copy', filename_list )

    def OnSpMove( self, filename_list ):
        return self.Sp_DispatchDrop( 'Cmd_Dir_Move', filename_list )

    #----------------------------------------
    def Sp_Dispatch( self, sp_func_name ):
        self.app.trace.info( 'WbTreePanel.Sp_Dispatch( %s ) event' % sp_func_name )
        item = self.tree_ctrl.GetSelection()
        if not item:
            return None

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        self.app.trace.info( 'WbTreePanel.Sp_Dispatch( %s ) calling' % sp_func_name )
        fn = getattr( handler, sp_func_name, None )
        if fn is None:
            print 'Not implemented', sp_func_name
            return None
        else:
            return fn()    

    def Sp_DispatchDrop( self, sp_func_name, filename_list ):
        self.app.trace.info( 'WbTreePanel.Sp_DispatchDrop( %s )' % sp_func_name )
        item = self.tree_ctrl.GetSelection()
        if not item:
            return None

        handler = self.tree_ctrl.GetPyData( item )
        if not handler:
            return None

        self.app.trace.info( 'WbTreePanel.Sp_DispatchDrop( %s ) calling' % sp_func_name )
        return getattr( handler, sp_func_name )( filename_list )

class SvnDropTarget(wx.PyDropTarget):
    def __init__( self, window ):
        wx.PyDropTarget.__init__( self )
        self.tree = window

        # specify the type of data we will accept
        self.df = wx.CustomDataFormat("WorkBench.svn_wc_path")
        self.data = wx.CustomDataObject(self.df)
        self.SetDataObject(self.data)

        self.start_item = None

    # some virtual methods that track the progress of the drag
    def OnEnter( self, x, y, d ):
        #print 'OnEnter: %d, %d, %d' % (x, y, d)
        return d

    def OnLeave( self ):
        #print 'OnLeave'
        if self.start_item is not None:
            #print 'OnLeave: have start_item'
            if self.start_item != self.tree.tree_ctrl.GetSelection():
                #print 'OnLeave: restoring start_item'
                self.tree.tree_ctrl.SelectItem( self.start_item )
                self.tree.tree_ctrl.EnsureVisible( self.start_item )
            self.start_item = None

    def OnDrop( self, x, y ):
        #print 'OnDrop: %d %d' % (x, y)
        item, flags = self.tree.tree_ctrl.HitTest( (x, y) )

        if (flags & wx.TREE_HITTEST_ONITEMLABEL) == 0:
            return False

        return True

    def OnDragOver( self, x, y, d ):
        #print 'OnDragOver: %d, %d, %d' % (x, y, d)
        item, flags = self.tree.tree_ctrl.HitTest( (x, y) )

        if self.start_item is None:
            self.start_item = self.tree.tree_ctrl.GetSelection()

        if flags & wx.TREE_HITTEST_ONITEMLABEL:
            if item != self.tree.tree_ctrl.GetSelection():
                self.tree.tree_ctrl.SelectItem( item )
                self.tree.tree_ctrl.EnsureVisible( item )
            return d

        return wx.DragNone

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData( self, x, y, d ):
        #print 'OnData: %d, %d, %d' % (x, y, d)

        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list of lines and give it to the viewer
            all_filenames = cPickle.loads( self.data.GetData() )
            if d == wx.DragCopy:
                self.tree.OnSpCopy( all_filenames )
            elif d == wx.DragMove:
                self.tree.OnSpMove( all_filenames )
            
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d



#--------------------------------------------------------------------------------
#
#
#    WbTreeCtrl
#
#
#--------------------------------------------------------------------------------
class WbTreeCtrl(wx.TreeCtrl):
    def __init__( self, parent, app ):
        self.app = app
        self.id_tree = wx.NewId()

        if wx.Platform == '__WXMSW__':
            style = wx.TR_HAS_BUTTONS
        else:
            style = wx.TR_HAS_BUTTONS|wx.TR_HIDE_ROOT
 
        wx.TreeCtrl.__init__( self, parent, self.id_tree, 
                                wx.DefaultPosition,
                                wx.DefaultSize,
                                style )

        self.item_last_used = None

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

    # Returns the window identifier for this control
    def getId( self ):
        return self.id_tree

    # Searches the child items of a tree item for the child that matches the
    # specified name
    # Returns the tree item id of the found item or None
    def getItemByName(self, item_parent, name):
        #Iterate through the child items looking for one with the correct name
        child_item, ctx = self.GetFirstChild( item_parent )

        if child_item and self.GetItemText( child_item ) == name:
            return child_item
        else:
            child_item, ctx = self.GetNextChild( item_parent, ctx )
            while child_item:
                if self.GetItemText( child_item ) == name:
                    return child_item

                next_child_item, ctx = self.GetNextChild( item_parent, ctx )
                if next_child_item == child_item:
                    self.app.log.debug("GetItemByName - Infinite loop detected... breaking")
                    break

                child_item = next_child_item

        self.app.log.debug("GetItemByName failed to find item")
        return None

    def OnCompareItems( self, a_item, b_item ):
        # sort case blind

        a_handler = self.GetPyData( a_item )
        a_pi = a_handler.getProjectInfo()

        b_handler = self.GetPyData( b_item )
        b_pi = b_handler.getProjectInfo()

        if a_handler.isProjectParent():
            # compare nodes in the root - projects
            return cmp( self.GetItemText( a_item ).lower(), self.GetItemText( b_item ).lower() )
        else:
            # compare children of projects
            # return cmp( a_pi.wc_path.lower(), b_pi.wc_path.lower() )
            return wb_torun_configspec.compare( a_pi.wc_path.lower().split( os.sep )[-1], b_pi.wc_path.lower().split( os.sep )[-1] )

#--------------------------------------------------------------------------------
#
#
#    TreeProjectItem
#
#
#--------------------------------------------------------------------------------
class TreeProjectItem:
    def __init__( self ):
        # true if this is the parent of a project tree
        self.is_project_parent = False

    def setIsProjectParent( self ):
        self.is_project_parent = True

    def isProjectParent( self ):
        return self.is_project_parent

    def getState( self ):
        raise wb_exceptions.InternalError( 'getState not implemented' )

    def getProjectInfo( self ):
        raise wb_exceptions.InternalError( 'getProjectInfo not implemented' )

    def getExpansion( self ):
        raise wb_exceptions.InternalError( 'getExpanding not implemented' )

    def getContextMenu( self, state ):
        raise wb_exceptions.InternalError( 'getContextMenu not implemented' )
        

class RootTreeItem(TreeProjectItem):
    def __init__( self ):
        TreeProjectItem.__init__( self )

    def getProjectInfo( self ):
        return None

    def getExpansion( self ):
        return []

    def getContextMenu( self, state ):
        menu = wx.Menu()

        menu.Append( wb_ids.id_Project_Add, T_('&Add Project') )

        return menu

    def getState( self ):
        return None

    def isProjectParent( self ):
        return False
