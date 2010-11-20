'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_frame.py

'''
import sys
import wx
import wx.stc
import logging

import wb_tree_panel
import wb_list_panel
import wb_list_panel_common
import wb_ids
import wb_exceptions
import wb_version
import wb_images
import wb_preferences_dialog
import wb_torun_setting_dialog
import wb_source_control_providers
import wb_platform_specific
import wb_bookmarks_dialogs
import wb_toolbars

import wb_config

class WbFrame(wx.Frame):
    status_general = 0
    status_search = 0    # use the general area
    status_progress = 1
    status_action = 2
    status_num_fields = 3
    status_widths = [-1, 150, -2]

    def __init__( self, app ):
        self.app = app
        title = T_('kSVN WorkBench')

        win_prefs = self.app.prefs.getWindow()

        extra_style = 0
        if win_prefs.maximized:
            extra_style = wx.MAXIMIZE

        wx.Frame.__init__(self, None, -1, title,
                win_prefs.frame_position,
                win_prefs.getFrameSize(),
                wx.DEFAULT_FRAME_STYLE|extra_style )

        # Reset the size after startup to workaround a potential
        # problem on OSX with incorrect first size event saving the
        # wrong size in the preferences
        wx.CallAfter( self.SetSize, win_prefs.getFrameSize() )
        
        self.menu_edit = wx.Menu()
        self.menu_edit.Append( wb_ids.id_SP_EditCopy, T_("&Copy"), T_("Copy Files") )
        self.menu_edit.Append( wb_ids.id_SP_EditCut, T_("&Cut"), T_("Cut Files") )
        self.menu_edit.Append( wb_ids.id_SP_EditPaste, T_("&Paste"), T_("Paste Files") )
        self.menu_edit.AppendSeparator()
        self.menu_edit.Append( wb_ids.id_ClearLog, T_("&Clear log"), T_("Clear the log window") )

        if wx.Platform != '__WXMAC__':
            self.menu_file = wx.Menu()
        else:
            self.menu_file = self.menu_edit

        self.menu_file.Append( wx.ID_PREFERENCES, T_("&Preferences..."), T_("Preferences") )
        self.menu_file.Append( wb_ids.id_Torun_Setting, T_("TSVN &Settings..."), T_("Customize the TSVN preferences") )
        self.menu_file.Append( wx.ID_EXIT, T_("E&xit"), T_("Exit the application") )

        self.menu_actions = wx.Menu()
        self.menu_actions.Append(  wb_ids.id_Command_Shell, T_('&Command Shell'), T_('Command Shell') )
        self.menu_actions.Append(  wb_ids.id_File_Browser, T_('&File Browser'), T_('File Browser') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append(  wb_ids.id_File_Edit, T_('Edit'), T_('Edit') )
        self.menu_actions.Append(  wb_ids.id_Shell_Open, T_('Open'), T_('Open') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBase, T_('Diff WC vs. BASE...'), T_('Diff WC vs. BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...'), T_('Diff WC vs. HEAD...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...'), T_('Diff WC vs. branch origin BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...'), T_('Diff WC vs. branch origin HEAD...') )

        self.menu_actions_conflict = wx.Menu()
        self.menu_actions.AppendMenu( wb_ids.id_SP_ConflictMenu, T_('Conflict'), self.menu_actions_conflict )
        self.menu_actions_conflict.Append( wb_ids.id_SP_DiffOldMine, T_('Diff Conflict Old vs. Mine...'), T_('Diff Conflict Old vs. Mine...') )
        self.menu_actions_conflict.Append( wb_ids.id_SP_DiffMineNew, T_('Diff Conflict Mine vs. New...'), T_('Diff Conflict Mine vs. New...') )
        self.menu_actions_conflict.Append( wb_ids.id_SP_DiffOldNew, T_('Diff Conflict Old vs. New...'), T_('Diff Conflict Old vs. New...') )
        self.menu_actions_conflict.AppendSeparator()
        self.menu_actions_conflict.Append( wb_ids.id_SP_Resolved, T_('Resolved Conflict'), T_('Resolved Conflict') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Annotate, T_('Annotate...'), T_('Annotate...') )
        self.menu_actions.Append( wb_ids.id_SP_History, T_('Log history...'), T_('Log history...') )
        self.menu_actions.Append( wb_ids.id_SP_Info, T_('Information...'), T_('Information...') )
        self.menu_actions.Append( wb_ids.id_SP_Properties, T_('Properties...'), T_('Properties...') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Update, T_('Update'), T_('Update') )
        self.menu_actions.Append( wb_ids.id_SP_UpdateTo, T_('Update to...'), T_('Update to...') )
        self.menu_actions.Append( wb_ids.id_SP_Checkout, T_('Checkout'), T_('Checkout') )
        self.menu_actions.Append( wb_ids.id_SP_CheckoutTo, T_('Checkout to...'), T_('Checkout to...') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Checkin, T_('Checkin...'), T_('Checkin...') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Lock, T_('Lock...'), T_('Lock...') )
        self.menu_actions.Append( wb_ids.id_SP_Unlock, T_('Unlock...'), T_('Unlock...') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_NewFile, T_('New File...'), T_('New File...') )
        self.menu_actions.Append( wb_ids.id_SP_Mkdir, T_('Make directory...'), T_('Make directory...') )
        self.menu_actions.Append( wb_ids.id_SP_Add, T_('Add'), T_('Add') )
        self.menu_actions.Append( wb_ids.id_SP_Rename, T_('Rename...'), T_('Rename') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Delete, T_('Delete...'), T_('Delete') )
        self.menu_actions.Append( wb_ids.id_SP_Revert, T_('Revert...'), T_('Revert') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Cleanup, T_('Clean up'), T_('Clean up working copy') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_CreateTag, T_('Create Tag...'), T_('Create Tag') )
        self.menu_actions.Append( wb_ids.id_SP_CreateBranch, T_('Create Branch...'), T_('Create Branch') )

        self.menu_reports = wx.Menu()
        self.menu_reports.Append( wb_ids.id_SP_Report_LocksWc, T_('Working copy Locks...'), T_('Locks held in Working Copy') )
        self.menu_reports.Append( wb_ids.id_SP_Report_LocksRepos, T_('Repository Locks...'), T_('Locks held in Repository') )
        self.menu_reports.AppendSeparator()
        self.menu_reports.Append( wb_ids.id_SP_Checkin, T_('Changes...'), T_('Changes available for checkin') )
        self.menu_reports.Append( wb_ids.id_SP_Report_Updates, T_('Updates...'), T_('Updates available in the Repository') )
        self.menu_reports.Append( wb_ids.id_SP_Report_BranchChanges, T_('Branch changes...'), T_('Files changed in this branch') )

        self.menu_view = wx.Menu()
        self.menu_view.AppendCheckItem( wb_ids.id_View_ControlledFiles, T_("Show &Controlled files"), T_("Show Controlled files") )
        self.menu_view.AppendCheckItem( wb_ids.id_View_UncontrolledFiles, T_("Show &Uncontrolled files"), T_("Show Uncontrolled files") )
        self.menu_view.AppendCheckItem( wb_ids.id_View_IgnoredFiles, T_("Show &Ignored files"), T_("Show ignored files") )
        self.menu_view.AppendCheckItem( wb_ids.id_View_OnlyChanges, T_("Show &Only changed files"), T_("Filter out unchanged files") )
        self.menu_view.AppendSeparator()
        self.menu_view.AppendCheckItem( wb_ids.id_View_Recursive, T_("Show &Recursive files"), T_("Show recursive files") )
        self.menu_view.AppendSeparator()
        self.menu_view.AppendCheckItem( wb_ids.id_View_Diff_WbDiff, T_('Use WorkBench Diff') )
        self.menu_view.AppendCheckItem( wb_ids.id_View_Diff_ExtGuiDiff, T_('Use External GUI Diff') )
        self.menu_view.AppendCheckItem( wb_ids.id_View_Diff_ExtTextDiff, T_('Use External Text Diff') )
        self.menu_view.AppendCheckItem( wb_ids.id_View_Diff_SvnDiff, T_('Use SVN Diff') )
        self.menu_view.AppendSeparator()
        self.menu_view.Append( wb_ids.id_View_Refresh, T_("&Refresh\tF5"), T_("Refresh display") )
        self.menu_view.AppendCheckItem( wb_ids.id_View_AutoRefresh, T_("&Automatic Refresh"), T_("Automatic refresh") )


        self.bookmark_menu_tree = BookmarkMenu('')
        self.all_bookmarks_id_to_pi = {}
        self.all_bookmark_top_level_menu_ids = []
        self.all_bookmark_folders = {}
        self.all_bookmark_folders2 = {}

        self.menu_bookmarks = wx.Menu()
        self.menu_bookmarks.Append( wb_ids.id_Bookmark_Add, T_('Add'), T_('Add Bookmark') )
        self.menu_bookmarks.Append( wb_ids.id_Bookmark_Manage, T_('Manage...'), T_('Manage Bookmarks') )
        self.menu_bookmarks.AppendSeparator()

        self.__bookmarkMenuReorder()

        self.menu_project = wx.Menu()
        self.menu_project.Append( wb_ids.id_Project_Add, T_('Add...'), T_('Project Add') )
        self.menu_project.Append( wb_ids.id_Project_Update, T_('Settings...'), T_('Project Settings') )
        self.menu_project.AppendSeparator()
        self.menu_project.Append( wb_ids.id_Project_Delete, T_('Delete...'), T_('Delete Project') )

        self.menu_help = wx.Menu()
        self.menu_help.Append( wx.ID_ABOUT, T_("&About..."), T_("About the application") )

        self.menu_bar = wx.MenuBar()
        if wx.Platform != '__WXMAC__':
            self.menu_bar.Append( self.menu_file, T_("&File") )
        self.menu_bar.Append( self.menu_edit, T_("&Edit") )
        self.menu_bar.Append( self.menu_view, T_("&View") )
        self.menu_bar.Append( self.menu_actions, T_("&Actions") )
        self.menu_bar.Append( self.menu_reports, T_("&Reports") )
        self.menu_bar.Append( self.menu_bookmarks, T_("&Bookmarks") )
        self.menu_bar.Append( self.menu_project, T_("&Project") )
        self.menu_bar.Append( self.menu_help, T_("&Help") )

        self.SetMenuBar( self.menu_bar )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png') )

        # Initialize tool bar
        
        # Remark: The order of the groups and their activity (enabled/disabled)
        # is managed in the preferences...
        self.compileToolBar()
        
        # Add the status bar
        s = self.CreateStatusBar()
        s.SetFieldsCount( WbFrame.status_num_fields )
        s.SetStatusWidths( WbFrame.status_widths )
        s.SetStatusText( T_("Work Bench"), WbFrame.status_general )
        s.SetStatusText( "", WbFrame.status_progress )
        s.SetStatusText( T_("Ready"), WbFrame.status_action )
        if WbFrame.status_search != WbFrame.status_general:
            s.SetStatusText( "", WbFrame.status_search )

        # Create the splitter windows
        if 'wxMac' in wx.PlatformInfo:
            style = wx.SP_LIVE_UPDATE | wx.SP_3DSASH
        else:
            style = wx.SP_LIVE_UPDATE
        self.h_split = wx.SplitterWindow( self, -1, style=style )
        self.v_split = wx.SplitterWindow( self.h_split, -1, style=style )

        # Make sure the splitters can't be removed by setting a minimum size
        self.v_split.SetMinimumPaneSize( 100 )
        self.h_split.SetMinimumPaneSize( 100 )

        # Create the main panels
        self.log_panel = LogCtrlPanel( self.app, self.h_split )
        self.log_panel.SetZoom( win_prefs.zoom )
        self.list_panel = wb_list_panel.WbListPanel( self.app, self, self.v_split )
        self.tree_panel = wb_tree_panel.WbTreePanel( self.app, self, self.v_split )

        # Fixup the tab order that results from creating the tree and
        # list panels in the wrong order
        self.list_panel.MoveAfterInTabOrder( self.tree_panel )

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        size = self.GetClientSize()

        h_sash_pos = max( 200, int( size.height * win_prefs.h_sash_ratio) )
        v_sash_pos = max( 200, int( size.width  * win_prefs.v_sash_ratio) )
        
        # Arrange the panels with the splitter windows
        self.v_split.SplitVertically( self.tree_panel, self.list_panel, v_sash_pos )
        self.h_split.SplitHorizontally( self.v_split, self.log_panel, h_sash_pos )

        # for some unknown reason MENU events get blocked by tree and list controls
        for event_source in [self, self.tree_panel.tree_ctrl, self.list_panel.list_ctrl]:
            # Set up the event handlers
            wx.EVT_MENU( event_source, wx.ID_ABOUT, try_wrapper( self.OnCmdAbout ) )
            wx.EVT_MENU( event_source, wx.ID_PREFERENCES, try_wrapper( self.OnCmdPreferences ) )
            wx.EVT_MENU( event_source, wb_ids.id_Torun_Setting, try_wrapper( self.OnCmdTorunSettings ) )
            wx.EVT_MENU( event_source, wx.ID_EXIT, try_wrapper( self.OnCmdExit ) )
            wx.EVT_MENU( event_source, wb_ids.id_ClearLog, try_wrapper( self.OnCmdClearLog ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_Refresh, try_wrapper( self.OnRefresh ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_AutoRefresh, try_wrapper( self.OnToggleAutoRefresh ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_AutoRefresh, try_wrapper( self.OnUpdateAutoRefresh ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_ControlledFiles, try_wrapper( self.OnToggleViewControlled ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_ControlledFiles, try_wrapper( self.OnUpdateViewControlled ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_UncontrolledFiles, try_wrapper( self.OnToggleViewUncontrolled ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_UncontrolledFiles, try_wrapper( self.OnUpdateViewUncontrolled ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_IgnoredFiles, try_wrapper( self.OnToggleViewIgnored ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_IgnoredFiles, try_wrapper( self.OnUpdateViewIgnored ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_Recursive, try_wrapper( self.OnToggleViewRecursive ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_Recursive, try_wrapper( self.OnUpdateViewRecursive ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_OnlyChanges, try_wrapper( self.OnToggleViewOnlyChanges ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_OnlyChanges, try_wrapper( self.OnUpdateViewOnlyChanges ) )

            wx.EVT_MENU( event_source, wb_ids.id_SP_EditCopy, self.app.eventWrapper( self.OnSpEditCopy ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_SP_EditCopy, self.app.eventWrapper( self.OnUpdateUiSpEditCopy ) )
            wx.EVT_MENU( event_source, wb_ids.id_SP_EditCut, self.app.eventWrapper( self.OnSpEditCut ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_SP_EditCut, self.app.eventWrapper( self.OnUpdateUiSpEditCut ) )
            wx.EVT_MENU( event_source, wb_ids.id_SP_EditPaste, self.app.eventWrapper( self.OnSpEditPaste ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_SP_EditPaste, self.app.eventWrapper( self.OnUpdateUiSpEditPaste ) )

            wx.EVT_MENU( event_source, wb_ids.id_View_Diff_WbDiff, self.app.eventWrapper( self.OnViewDiffWbDiff ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_Diff_WbDiff, self.app.eventWrapper( self.OnUpdateUiViewDiffWbDiff ) )
            wx.EVT_MENU( event_source, wb_ids.id_View_Diff_ExtGuiDiff, self.app.eventWrapper( self.OnViewDiffExtGuiDiff ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_Diff_ExtGuiDiff, self.app.eventWrapper( self.OnUpdateUiViewDiffExtGuiDiff ) )
            wx.EVT_MENU( event_source, wb_ids.id_View_Diff_ExtTextDiff, self.app.eventWrapper( self.OnViewDiffExtTextDiff ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_Diff_ExtTextDiff, self.app.eventWrapper( self.OnUpdateUiViewDiffExtTextDiff ) )
            wx.EVT_MENU( event_source, wb_ids.id_View_Diff_SvnDiff, self.app.eventWrapper( self.OnViewDiffSvnDiff ) )
            wx.EVT_UPDATE_UI( event_source, wb_ids.id_View_Diff_SvnDiff, self.app.eventWrapper( self.OnUpdateUiViewDiffSvnDiff ) )

        wx.EVT_MENU( self, wb_ids.id_File_Edit, try_wrapper( self.OnFileEdit ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_File_Edit, try_wrapper( self.OnUpdateUiFileEdit ) )
        wx.EVT_MENU( self, wb_ids.id_Shell_Open, try_wrapper( self.OnShellOpen ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_Shell_Open, try_wrapper( self.OnUpdateUiShellOpen ) )

        wx.EVT_MENU( self, wb_ids.id_Command_Shell, try_wrapper( self.OnCommandShell ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_Command_Shell, try_wrapper( self.OnUpdateUiCommandShell ) )
        wx.EVT_MENU( self, wb_ids.id_File_Browser, try_wrapper( self.OnFileBrowser ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_File_Browser, try_wrapper( self.OnUpdateUiFileBrowser ) )

        wx.EVT_MENU( self, wb_ids.id_SP_Add, self.app.eventWrapper( self.OnSpAdd ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Add, self.app.eventWrapper( self.OnUpdateUiSpAdd ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnSpAnnotate ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnUpdateUiSpAnnotate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Checkin, self.app.eventWrapper( self.OnSpCheckin ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Checkin, self.app.eventWrapper( self.OnUpdateUiSpCheckin ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Checkout, self.app.eventWrapper( self.OnSpCheckout ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Checkout, self.app.eventWrapper( self.OnUpdateUiSpCheckout ) )
        wx.EVT_MENU( self, wb_ids.id_SP_CheckoutTo, self.app.eventWrapper( self.OnSpCheckoutTo ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_CheckoutTo, self.app.eventWrapper( self.OnUpdateUiSpCheckoutTo ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Cleanup, self.app.eventWrapper( self.OnSpCleanup ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Cleanup, self.app.eventWrapper( self.OnUpdateUiSpCleanup ) )
        wx.EVT_MENU( self, wb_ids.id_SP_CreateTag, self.app.eventWrapper( self.OnSpCreateTag ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_CreateTag, self.app.eventWrapper( self.OnUpdateUiSpCreateTag ) )
        wx.EVT_MENU( self, wb_ids.id_SP_CreateBranch, self.app.eventWrapper( self.OnSpCreateBranch ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_CreateBranch, self.app.eventWrapper( self.OnUpdateUiSpCreateBranch ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Delete, self.app.eventWrapper( self.OnSpDelete ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Delete, self.app.eventWrapper( self.OnUpdateUiSpDelete ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffMineNew, self.app.eventWrapper( self.OnSpDiffMineNew ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffMineNew, self.app.eventWrapper( self.OnUpdateUiSpDiffMineNew ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffOldMine, self.app.eventWrapper( self.OnSpDiffOldMine ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffOldMine, self.app.eventWrapper( self.OnUpdateUiSpDiffOldMine ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffOldNew, self.app.eventWrapper( self.OnSpDiffOldNew ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffOldNew, self.app.eventWrapper( self.OnUpdateUiSpDiffOldNew ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBase, self.app.eventWrapper( self.OnSpDiffWorkBase ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffWorkBase, self.app.eventWrapper( self.OnUpdateUiSpDiffWorkBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkHead, self.app.eventWrapper( self.OnSpDiffWorkHead ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffWorkHead, self.app.eventWrapper( self.OnUpdateUiSpDiffWorkHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginBase, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginBase ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffWorkBranchOriginBase, self.app.eventWrapper( self.OnUpdateUiSpDiffWorkBranchOriginBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginHead, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginHead ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_DiffWorkBranchOriginHead, self.app.eventWrapper( self.OnUpdateUiSpDiffWorkBranchOriginHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnSpHistory ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnUpdateUiSpHistory ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Info, self.app.eventWrapper( self.OnSpInfo ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Info, self.app.eventWrapper( self.OnUpdateUiSpInfo ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Lock, self.app.eventWrapper( self.OnSpLock ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Lock, self.app.eventWrapper( self.OnUpdateUiSpLock ) )
        wx.EVT_MENU( self, wb_ids.id_SP_NewFile, self.app.eventWrapper( self.OnSpNewFile ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_NewFile, self.app.eventWrapper( self.OnUpdateUiSpNewFile ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Mkdir, self.app.eventWrapper( self.OnSpMkdir ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Mkdir, self.app.eventWrapper( self.OnUpdateUiSpMkdir ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Properties, self.app.eventWrapper( self.OnSpProperties ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Properties, self.app.eventWrapper( self.OnUpdateUiSpProperties ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Rename, self.app.eventWrapper( self.OnSpRename ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Rename, self.app.eventWrapper( self.OnUpdateUiSpRename ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Resolved, self.app.eventWrapper( self.OnSpResolved ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Resolved, self.app.eventWrapper( self.OnUpdateUiSpResolved ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Revert, self.app.eventWrapper( self.OnSpRevert ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Revert, self.app.eventWrapper( self.OnUpdateUiSpRevert ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Unlock, self.app.eventWrapper( self.OnSpUnlock ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Unlock, self.app.eventWrapper( self.OnUpdateUiSpUnlock ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Update, self.app.eventWrapper( self.OnSpUpdate ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Update, self.app.eventWrapper( self.OnUpdateUiSpUpdate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_UpdateTo, self.app.eventWrapper( self.OnSpUpdateTo ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_UpdateTo, self.app.eventWrapper( self.OnUpdateUiSpUpdateTo ) )

        wx.EVT_MENU( self, wb_ids.id_SP_Report_Updates, self.app.eventWrapper( self.OnSpReportUpdates ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Report_Updates, self.app.eventWrapper( self.OnUpdateUiSpReportUpdates ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Report_LocksWc, self.app.eventWrapper( self.OnSpReportLocksWc ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Report_LocksWc, self.app.eventWrapper( self.OnUpdateUiSpReportLocksWc ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Report_LocksRepos, self.app.eventWrapper( self.OnSpReportLocksRepos ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Report_LocksRepos, self.app.eventWrapper( self.OnUpdateUiSpReportLocksRepos ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Report_BranchChanges, self.app.eventWrapper( self.OnSpReportBranchChanges ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_SP_Report_BranchChanges, self.app.eventWrapper( self.OnUpdateUiSpReportBranchChanges ) )

        wx.EVT_MENU( self, wb_ids.id_Project_Add, try_wrapper( self.app.eventWrapper( self.tree_panel.OnProjectAdd ) ) )
        wx.EVT_MENU( self, wb_ids.id_Project_Update, try_wrapper( self.app.eventWrapper( self.tree_panel.OnProjectUpdate ) ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_Project_Update, try_wrapper( self.app.eventWrapper( self.OnUpdateUiProjectUpdateOrDelete ) ) )
        wx.EVT_MENU( self, wb_ids.id_Project_Delete, try_wrapper( self.app.eventWrapper( self.tree_panel.OnProjectDelete ) ) )
        wx.EVT_UPDATE_UI( self, wb_ids.id_Project_Delete, try_wrapper( self.app.eventWrapper( self.OnUpdateUiProjectUpdateOrDelete ) ) )

        wx.EVT_MENU( self, wb_ids.id_Bookmark_Add, try_wrapper( self.OnBookmarkAdd ) )
        wx.EVT_MENU( self, wb_ids.id_Bookmark_Manage, try_wrapper( self.OnBookmarkManage ) )

        wx.EVT_SIZE( self, self.OnSize )
        wx.EVT_MOVE( self, self.OnMove )

        wx.EVT_SIZE( self.v_split, self.OnVertSize )
        wx.EVT_SIZE( self.h_split, self.OnHorizSize )
        wx.EVT_SPLITTER_SASH_POS_CHANGED( self.v_split, -1, self.OnVertSashPositionChanged )
        wx.EVT_SPLITTER_SASH_POS_CHANGED( self.h_split, -1, self.OnHorizSashPositionChanged )

        wx.stc.EVT_STC_ZOOM(self, -1, self.OnZoom)
        
        wx.EVT_CLOSE(self, try_wrapper( self.OnCloseWindow ))

        # default to the tree panel as the first set_focus can go missing
        self.event_handler = None

        self.ui_state_tree = None
        self.ui_state_list = None
        self.ui_state_focus = None

        self.setEventHandler( self.tree_panel )

        # need to set focus away from the filter controls
        # should not have to reach through these levels
        self.list_panel.list_ctrl.SetFocus()


    def compileToolBar( self ):
        #
        # Create the toolbar, if it is enabled.
        #
        toolbar_prefs = self.app.prefs.getToolbar()
        if not toolbar_prefs.toolbar_enable:
            return

        if toolbar_prefs.horizontal_orientation:
            tb_style = wx.TB_HORIZONTAL

        else:
            tb_style = wx.TB_VERTICAL

        toolbar = self.CreateToolBar( name="main", style=tb_style )
        toolbar.SetToolBitmapSize( (toolbar_prefs.bitmap_size, toolbar_prefs.bitmap_size) )

        wb_toolbars.toolbar_main.populateToolBar( toolbar_prefs, toolbar )

        toolbar.Realize()

    def setEventHandler( self, handler ):
        if wb_config.debug_selection:
            print 'ZF: setEventHandler from %r' % self.event_handler
            print 'ZF: setEventHandler   to %r' % handler
            import wb_debug
            wb_debug.printStack( '     ' )

        self.app.debugShowCallers( 20 )

        if self.event_handler is not handler:
            self.event_handler = handler
            self.clearUpdateUiState()

    def clearEventHandler( self ):
        self.app.log.debug( 'clearEventHandler from %r to None' % self.event_handler )
        if wb_config.debug_selection: print 'ZF: clearEventHandler from %r to None' % self.event_handler
        self.event_handler = None
        self.clearUpdateUiState()

    def isEventHandler( self, handler ):
        return self.event_handler is handler

    # Status bar settings
    def setStatus( self, text ):
        self.GetStatusBar().SetStatusText( text, WbFrame.status_general )

    def setProgress( self, text ):
        self.GetStatusBar().SetStatusText( text, WbFrame.status_progress )

    def setAction( self, text ):
        self.GetStatusBar().SetStatusText( text, WbFrame.status_action )

    def setSearch( self, text ):
        self.GetStatusBar().SetStatusText( text, WbFrame.status_search )

    def savePreferences( self ):
        win_prefs = self.app.prefs.getWindow()
        # Size and Position are already saved
        win_prefs.maximized = self.IsMaximized()

        self.tree_panel.savePreferences()
        self.list_panel.savePreferences()

    # Handler for the Exit menu command
    def OnCmdExit(self, event):
        self.Close()

    # Handler for the About menu command
    def OnCmdAbout(self, event):
        ver_str = ('%d.%d.%d-%d\n' %
                    (wb_version.major, wb_version.minor,
                     wb_version.patch, wb_version.build))
        str_message =    ((T_('kSVN version: %s') % ver_str) +
                '\n' + wb_source_control_providers.getProviderAboutStrings() +
                'wxPython %d.%d.%d.%d %s' % wx.VERSION +
                '\nPython %d.%d.%d %s %d\n' % sys.version_info +
                T_('\nCopyright Barry Scott (c) 2003-2009. All rights reserved') +
                T_('\nCopyright ccc (c) 2010. All rights reserved')
                )
        wx.LogMessage( str_message )

    def OnCmdPreferences( self, event ):
        pref_dialog = wb_preferences_dialog.PreferencesDialog( self, self.app )
        rc = pref_dialog.ShowModal()
        if rc == wx.ID_OK:
            self.app.savePreferences()

        self.list_panel.updateHandler()
        self.refreshFrame()

    def OnCmdTorunSettings( self, event ):
        pref_dialog = wb_torun_setting_dialog.TorunSettingDialog( self, self.app )
        rc = pref_dialog.ShowModal()
        if rc == wx.ID_OK:
            self.app.savePreferences()

        self.list_panel.updateHandler()
        self.refreshFrame()

    def OnUnlockedUi( self ):
        self.setAction( T_('Ready') )
        self.tree_panel.updateTree()

    def OnSize( self, event ):
        pref = self.app.prefs.getWindow()

        if not self.IsMaximized():
            pref.setFrameSize( self.GetSize() )

        event.Skip()

    def OnMove( self, event ):
        pref = self.app.prefs.getWindow()

        if not self.IsMaximized() and not self.IsIconized():
            # don't use the event.GetPosition() as it
            # is off by the window frame thickness
            pt = self.GetPosition()
            pref.frame_position = pt

        pref.maximized = self.IsMaximized()

        event.Skip()

    def OnHorizSashPositionChanged( self, event ):
        _, h = self.h_split.GetClientSizeTuple()
        win_prefs = self.app.prefs.getWindow()
        win_prefs.h_sash_ratio = float( event.GetSashPosition() ) / float( h )
        event.Skip()

    def OnVertSashPositionChanged( self, event ):
        w, _ = self.v_split.GetClientSizeTuple()
        win_prefs = self.app.prefs.getWindow()
        win_prefs.v_sash_ratio = float( event.GetSashPosition() ) / float( w )
        event.Skip()

    def OnHorizSize( self, event ):
        win_prefs = self.app.prefs.getWindow()
        _, h = self.h_split.GetClientSizeTuple()
        self.h_split.SetSashPosition( max( 200, int( h * win_prefs.h_sash_ratio ) ) )
        event.Skip()

    def OnVertSize( self, event ):
        win_prefs = self.app.prefs.getWindow()
        w, _ = self.v_split.GetClientSizeTuple()
        self.v_split.SetSashPosition( max( 200, int( w * win_prefs.v_sash_ratio ) ) )
        event.Skip()

    def OnZoom(self, evt):
        win_prefs = self.app.prefs.getWindow()
        win_prefs.zoom = self.log_panel.GetZoom()
        
    #------------------------------------------------------------------------
    def OnActivateApp( self, is_active ):
        if is_active and self.app.prefs.getView().auto_refresh:
            self.refreshFrame()

    def OnToggleAutoRefresh( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.auto_refresh = not view_prefs.auto_refresh
        if view_prefs.auto_refresh:
            self.refreshFrame()

    def OnUpdateAutoRefresh( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.auto_refresh )

    def OnToggleViewControlled( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.view_controlled = not view_prefs.view_controlled
        self.refreshFrame()

    def OnUpdateViewControlled( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.view_controlled )

    def OnToggleViewUncontrolled( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.view_uncontrolled = not view_prefs.view_uncontrolled
        self.refreshFrame()

    def OnUpdateViewUncontrolled( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.view_uncontrolled )

    def OnToggleViewIgnored( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.view_ignored = not view_prefs.view_ignored
        self.refreshFrame()

    def OnUpdateViewIgnored( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.view_ignored )

    def OnToggleViewRecursive( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.view_recursive = not view_prefs.view_recursive
        self.refreshFrame()

    def OnUpdateViewRecursive( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.view_recursive )

    def OnToggleViewOnlyChanges( self, event ):
        view_prefs = self.app.prefs.getView()
        view_prefs.view_onlychanges = not view_prefs.view_onlychanges
        self.refreshFrame()

    def OnUpdateViewOnlyChanges( self, event ):
        view_prefs = self.app.prefs.getView()
        event.Check( view_prefs.view_onlychanges )

    def OnViewDiffWbDiff( self, event ):
        self.app.prefs.getDiffTool().diff_tool_mode = 'built-in'
        self.app.prefs.writePreferences()

    def OnUpdateUiViewDiffWbDiff( self, event ):
        event.Check( self.app.prefs.getDiffTool().diff_tool_mode == 'built-in' )

    def OnViewDiffExtGuiDiff( self, event ):
        self.app.prefs.getDiffTool().diff_tool_mode = 'external-gui-diff'
        self.app.prefs.writePreferences()

    def OnUpdateUiViewDiffExtGuiDiff( self, event ):
        event.Enable( self.app.prefs.getDiffTool().gui_diff_tool != '' )
        event.Check( self.app.prefs.getDiffTool().diff_tool_mode == 'external-gui-diff' )

    def OnViewDiffExtTextDiff( self, event ):
        self.app.prefs.getDiffTool().diff_tool_mode = 'external-shell-diff'
        self.app.prefs.writePreferences()

    def OnUpdateUiViewDiffExtTextDiff( self, event ):
        event.Enable( self.app.prefs.getDiffTool().shell_diff_tool != '' )
        event.Check( self.app.prefs.getDiffTool().diff_tool_mode == 'external-shell-diff' )

    def OnViewDiffSvnDiff( self, event ):
        self.app.prefs.getDiffTool().diff_tool_mode = 'svn-diff'
        self.app.prefs.writePreferences()

    def OnUpdateUiViewDiffSvnDiff( self, event ):
        event.Check( self.app.prefs.getDiffTool().diff_tool_mode == 'svn-diff' )

    def OnRefresh( self, event ):
        self.app.log.debug( 'OnRefresh()' )
        self.refreshFrame()

    def refreshFrame( self ):
        self.app.log.debug( 'WbFrame.refreshFrame()' )
        # tell the tree to refresh it will tell the list
        self.tree_panel.refreshTree()

    def expandSelectedTreeNode( self ):
        self.tree_panel.expandSelectedTreeNode()

    def selectTreeNodeInParent( self, filename ):
        self.tree_panel.selectTreeNodeInParent( filename )

    def selectTreeNode( self, filename ):
        self.tree_panel.selectTreeNode( filename )

    #------------------------------------------------------------------------
    def __bookmarkMenuReorder( self ):
        self.bookmark_menu_tree.unrealise()

        self.all_bookmarks_id_to_pi = {}

        bm_prefs = self.app.prefs.getBookmarks()
        self.bookmark_menu_tree = BookmarkMenu( '' )

        for bm_name in bm_prefs.getBookmarkNames():
            if bm_name == 'last position':
                continue

            pi = bm_prefs.getBookmark( bm_name )
            path = []
            if pi.menu_folder != '':
                path.append( pi.menu_folder )

            if pi.menu_folder2 != '':
                path.append( pi.menu_folder2 )

            if pi.menu_folder3 != '':
                path.append( pi.menu_folder3 )

            path.append( pi.menu_name )

            self.bookmark_menu_tree.add( path, pi )

        self.bookmark_menu_tree.realise( self.menu_bookmarks, self )

    def OnBookmarkAdd( self, event ):
        pi = self.tree_panel.getSelectionProjectInfo()
        if pi is None:
            return
        bm_prefs = self.app.prefs.getBookmarks()
 
        if not bm_prefs.hasBookmark( pi.url ):
            print T_('Adding bookmark to %s') % pi.wc_path
            bm_prefs.addBookmark( pi )

            self.__bookmarkMenuReorder()
            self.app.savePreferences()

    def OnBookmarkManage( self, event ):
        bookmarks = self.app.prefs.getBookmarks()
        dialog = wb_bookmarks_dialogs.BookmarkManageDialog( self, self.app, bookmarks )
        rc = dialog.ShowModal()
        if rc != wx.ID_OK:
            return

        dialog.setPreferences()
        self.app.savePreferences()
        self.__bookmarkMenuReorder()

    def OnBookmarkGoto( self, event ):
        self.tree_panel.gotoBookmark( self.all_bookmarks_id_to_pi[event.GetId()].wc_path )

    #------------------------------------------------------------------------
    def OnCmdClearLog( self, event ):
        self.log_panel.ClearLog()

    def OnCloseWindow( self, event ):
        if self.app.exitAppNow():
            self.Destroy()

    #------------------------------------------------------------------------
    def OnFileEdit( self, event ):
        return self.list_panel.OnFileEdit()

    def OnUpdateUiFileEdit( self, event ):
        self.getUpdateUiState()
        #self.ui_state_list.printState('OnUpdateUiFileEdit')
        #print 'isListHandler() => %r' % self.event_handler.isListHandler()
        event.Enable( self.ui_state_list.file_exists and self.event_handler.isListHandler())

    def OnShellOpen( self, event ):
        return self.list_panel.OnShellOpen()

    def OnUpdateUiShellOpen( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_list.file_exists and self.event_handler.isListHandler() )

    def OnCommandShell( self, event ):
        return self.tree_panel.OnCommandShell()

    def OnUpdateUiCommandShell( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists or self.ui_state_tree.is_folder )

    def OnFileBrowser( self, event ):
        return self.tree_panel.OnFileBrowser()

    def OnUpdateUiFileBrowser( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists or self.ui_state_tree.is_folder )

    def OnSpEditCopy( self, event ):
        return self.Sp_Dispatch( 'OnSpEditCopy' )

    def OnUpdateUiSpEditCopy( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.file_exists )

    def OnSpEditCut( self, event ):
        return self.Sp_Dispatch( 'OnSpEditCut' )

    def OnUpdateUiSpEditCut( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.file_exists )

    def OnSpEditPaste( self, event ):
        return self.Sp_Dispatch( 'OnSpEditPaste' )

    def OnUpdateUiSpEditPaste( self, event ):
        self.getUpdateUiState()
        event.Enable( self.app.hasPasteData() )

    #----------------------------------------
    def OnSpAdd( self, event ):
        return self.Sp_Dispatch( 'OnSpAdd' )

    def OnUpdateUiSpAdd( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.unversioned and self.ui_state_focus.file_exists )

    def OnSpAnnotate( self, event ):
        return self.Sp_Dispatch( 'OnSpAnnotate' )

    def OnUpdateUiSpAnnotate( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.versioned and (not self.ui_state_focus.is_folder) )

    def OnSpCheckin( self, event ):
        return self.Sp_Dispatch( 'OnSpCheckin' )

    def OnUpdateUiSpCheckin( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.need_checkin
                or (self.ui_state_focus.versioned
                    and self.event_handler is not None
                    and self.event_handler.isTreeHandler()) )

    def OnSpCheckout( self, event ):
        self.clearUpdateUiState()
        return self.tree_panel.OnSpCheckout()

    def OnUpdateUiSpCheckout( self, event ):
        self.getUpdateUiState()

        # this is a tree only command
        event.Enable( self.ui_state_tree.is_project_parent
                        and not self.ui_state_tree.file_exists
                        and self.ui_state_tree.versioned )

    def OnSpCheckoutTo( self, event ):
        self.clearUpdateUiState()
        return self.tree_panel.OnSpCheckoutTo()

    def OnUpdateUiSpCheckoutTo( self, event ):
        # same rules are checkout
        self.OnUpdateUiSpCheckout( event )

    def OnSpCleanup( self, event ):
        return self.Sp_Dispatch( 'OnSpCleanup' )

    def OnUpdateUiSpCleanup( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.file_exists and self.ui_state_focus.versioned )

    def OnSpCreateTag( self, event ):
        return self.Sp_Dispatch( 'OnSpCreateTag' )

    def OnUpdateUiSpCreateTag( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists and self.ui_state_tree.versioned )

    def OnSpCreateBranch( self, event ):
        return self.Sp_Dispatch( 'OnSpCreateBranch' )

    def OnUpdateUiSpCreateBranch( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists and self.ui_state_tree.versioned )

    def OnSpDelete( self, event ):
        return self.Sp_Dispatch( 'OnSpDelete' )

    def OnUpdateUiSpDelete( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.file_exists or self.ui_state_focus.versioned )

    def OnSpDiffMineNew( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffMineNew' )

    def OnUpdateUiSpDiffMineNew( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_list.conflict )

    def OnSpDiffOldMine( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffOldMine' )

    def OnUpdateUiSpDiffOldMine( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_list.conflict )

    def OnSpDiffOldNew( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffOldNew' )

    def OnUpdateUiSpDiffOldNew( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_list.conflict )

    def OnSpDiffWorkBase( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffWorkBase' )

    def OnUpdateUiSpDiffWorkBase( self, event ):
        self.getUpdateUiState()
        if self.ui_state_list is self.ui_state_focus:
            event.Enable( self.ui_state_list.modified )
        else:
            event.Enable( True )

    def OnSpDiffWorkHead( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffWorkHead' )

    def OnUpdateUiSpDiffWorkHead( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            if self.ui_state_list is self.ui_state_focus:
                event.Enable( self.ui_state_list.versioned and not self.ui_state_list.new_versioned )
            else:
                event.Enable( self.ui_state_tree.versioned )

    def OnSpDiffWorkBranchOriginBase( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffWorkBranchOriginBase' )

    def OnSpDiffWorkBranchOriginHead( self, event ):
        return self.Sp_Dispatch( 'OnSpDiffWorkBranchOriginHead' )

    def OnUpdateUiSpDiffWorkBranchOriginBase( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_list.versioned and not self.ui_state_list.new_versioned )

    def OnUpdateUiSpDiffWorkBranchOriginHead( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_list.versioned and not self.ui_state_list.new_versioned )

    def OnSpHistory( self, event ):
        return self.Sp_Dispatch( 'OnSpHistory' )

    def OnUpdateUiSpHistory( self, event ):
        self.getUpdateUiState()
        if wb_config.debug_selection_update: print 'ZF: OnUpdateUiSpHistory versioned %r handler %r' % (
                                                self.ui_state_focus.versioned, self.event_handler)
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.versioned and not self.ui_state_focus.new_versioned )

    def OnSpInfo( self, event ):
        return self.Sp_Dispatch( 'OnSpInfo' )

    def OnUpdateUiSpInfo( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.versioned )

    def OnSpLock( self, event ):
        return self.Sp_Dispatch( 'OnSpLock' )

    def OnUpdateUiSpLock( self, event ):
        self.getUpdateUiState()
        event.Enable( (not self.ui_state_focus.is_folder) and self.ui_state_focus.file_exists )

    def OnSpMkdir( self, event ):
        # always forward to the tree to handle
        return self.tree_panel.OnSpMkdir()

    def OnUpdateUiSpMkdir( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists )

    def OnSpNewFile( self, event ):
        return self.tree_panel.OnSpNewFile()

    def OnUpdateUiSpNewFile( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists )

    def OnSpProperties( self, event ):
        return self.Sp_Dispatch( 'OnSpProperties' )

    def OnUpdateUiSpProperties( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.versioned )

    def OnSpRename( self, event ):
        return self.Sp_Dispatch( 'OnSpRename' )

    def OnUpdateUiSpRename( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.file_exists )

    def OnSpReportUpdates( self, event ):
        return self.tree_panel.OnReportUpdates()

    def OnUpdateUiSpReportUpdates( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists )

    def OnSpReportLocksWc( self, event ):
        return self.Sp_Dispatch( 'OnReportLocksWc' )

    def OnUpdateUiSpReportLocksWc( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.versioned )

    def OnSpReportBranchChanges( self, event ):
        return self.tree_panel.OnReportBranchChanges()

    def OnUpdateUiSpReportBranchChanges( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_tree.file_exists )

    def OnSpReportLocksRepos( self, event ):
        return self.Sp_Dispatch( 'OnReportLocksRepos' )

    def OnUpdateUiSpReportLocksRepos( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_focus.versioned )

    def OnSpResolved( self, event ):
        return self.Sp_Dispatch( 'OnSpResolved' )

    def OnUpdateUiSpResolved( self, event ):
        self.getUpdateUiState()
        event.Enable( self.ui_state_list.conflict )

    def OnSpRevert( self, event ):
        return self.Sp_Dispatch( 'OnSpRevert' )

    def OnUpdateUiSpRevert( self, event ):
        self.getUpdateUiState()
        if self.ui_state_focus.need_checkout:
            event.Enable( False )
        else:
            event.Enable( self.ui_state_focus.revertable )

    def OnSpUnlock( self, event ):
        return self.Sp_Dispatch( 'OnSpUnlock' )

    def OnUpdateUiSpUnlock( self, event ):
        self.getUpdateUiState()
        event.Enable( (not self.ui_state_focus.is_folder) and self.ui_state_focus.file_exists )

    def OnSpUpdate( self, event ):
        return self.Sp_Dispatch( 'OnSpUpdate' )

    def OnUpdateUiSpUpdate( self, event ):
        self.getUpdateUiState()

        if self.ui_state_focus.need_checkout:
            import wb_subversion_tree_handler
            handler = self.tree_panel.getSelectionProjectHandler()
            if isinstance(handler, wb_subversion_tree_handler.SubversionProject):
                event.Enable( self.ui_state_focus.versioned )
            else:
                event.Enable(True)
        elif self.ui_state_focus.is_project_parent:
            handler = self.tree_panel.getSelectionProjectHandler()
            import wb_subversion_tree_handler
            if isinstance(handler, wb_subversion_tree_handler.SubversionProject):
                event.Enable( self.ui_state_focus.versioned and self.ui_state_focus.file_exists )
            else:
                event.Enable(True)
        else:
            import wb_subversion_tree_handler
            handler = self.tree_panel.getSelectionProjectHandler()
            if isinstance(handler, wb_subversion_tree_handler.SubversionProject):
                event.Enable( self.ui_state_focus.versioned )
            else:
                event.Enable(True)

    def OnUpdateUiProjectUpdateOrDelete( self, event ):
        handler = self.tree_panel.getSelectionProjectHandler()
        if handler and handler.isProjectParent():
            event.Enable( True )
        else:
            event.Enable( False )

    def OnSpUpdateTo( self, event ):
        return self.Sp_Dispatch( 'OnSpUpdateTo' )

    def OnUpdateUiSpUpdateTo( self, event ):
        self.OnUpdateUiSpUpdate(event)

    #----------------------------------------
    def Sp_Dispatch( self, sp_func_name ):
        self.clearUpdateUiState()

        if self.event_handler is None:
            print 'No event_handler, cannot call %r' % (sp_func_name,)
            return None

        fn = getattr( self.event_handler, sp_func_name, None )
        if fn is None:
            print 'Not implemented: %r in %r' % (sp_func_name, self.event_handler)
            return None
        else:
            return fn()

    def getUpdateUiState( self ):
        all_debug_messages = []
        if self.ui_state_tree is None:
            self.ui_state_tree = self.tree_panel.getUpdateUiState()
            if self.ui_state_tree is None:
                self.ui_state_tree = wb_tree_panel.TreeState( True )
            all_debug_messages.append( 'tree place_holder %s' % self.ui_state_tree.place_holder )

        if self.ui_state_list is None:
            self.ui_state_list = self.list_panel.getUpdateUiState()
            if self.ui_state_list is None:
                self.ui_state_list = wb_list_panel_common.ListItemState( True )
            all_debug_messages.append( 'list place_holder %s' % self.ui_state_list.place_holder )

        if self.ui_state_focus is None:
            if self.event_handler is None:
                all_debug_messages.append( 'event_handler is None set tree' )
                self.ui_state_focus = self.ui_state_tree
            elif self.event_handler.isTreeHandler():
                all_debug_messages.append( 'event_handler is Tree set tree' )
                self.ui_state_focus = self.ui_state_tree
            else:
                all_debug_messages.append( 'event_handler is List set list' )
                self.ui_state_focus = self.ui_state_list
            all_debug_messages.append( 'focus place_holder %s' % self.ui_state_focus.place_holder )

        if wb_config.debug_selection and len(all_debug_messages)>0:
            print 'ZF: getUpdateUiState() ------------------------------'
            for message in all_debug_messages:
                print '    %s' %message

    def clearUpdateUiState( self ):
        if wb_config.debug_selection: print 'ZF: clearUpdateUiState()'
        self.ui_state_tree = None
        self.ui_state_list = None
        self.ui_state_focus = None

#--------------------------------------------------------------------------------
class LogCtrlPanel(wx.Panel):
    def __init__( self, app, parent ):
        wx.Panel.__init__(self, parent, -1)

        self.app = app
        self.text_ctrl = StyledLogCtrl( self.app, self )

        # Redirect the console IO to this panel
        sys.stdin = file( wb_platform_specific.getNullDevice(), 'r' )
        if self.app.isStdIoRedirect():
            sys.stdout = self
            sys.stderr = self

        # Redirect log to the Log panel
        log_handler = LogHandler( self.text_ctrl )
        self.app.log.addHandler( log_handler )

        wx.EVT_SIZE( self, wb_exceptions.TryWrapper( self.app.log, self.OnSize ) )


    #---------- Event handlers ------------------------------------------------------------

    def OnSize( self, event ):
        self.text_ctrl.SetWindowSize( self.GetSize() )

    #---------- Public methods ------------------------------------------------------------

    def write( self, string ):
        # only allowed to use GUI objects on the foreground thread
        if not self.app.isMainThread():
            self.app.foregroundProcess( self.write, (string,) )
            return

        if string[:6] == 'Error:':
            self.text_ctrl.WriteError(string)
        elif string[:5] == 'Info:':
            self.text_ctrl.WriteInfo(string)
        elif string[:8] == 'Warning:':
            self.text_ctrl.WriteWarning(string)
        elif string[:5] == 'Crit:':
            self.text_ctrl.WriteCritical(string)
        else:
            self.text_ctrl.WriteNormal(string)

        if not self.app.isStdIoRedirect():
            sys.__stdout__.write( string )

    def close( self ):
        pass

    def ClearLog( self ):
        self.text_ctrl.ClearText()

    def GetZoom(self):
        return self.text_ctrl.GetZoom()

    def SetZoom(self, zoom):
        self.text_ctrl.SetZoom(zoom)

#--------------------------------------------------------------------------------
class LogHandler(logging.Handler):
    def __init__( self, log_ctrl ):
        self.log_ctrl = log_ctrl
        logging.Handler.__init__( self )

    def emit( self, record ):
        try:
            msg = self.format(record) + '\n'
            level = record.levelno
            if level >= logging.CRITICAL:
                self.log_ctrl.WriteCritical( msg )
            elif level >= logging.ERROR:
                self.log_ctrl.WriteError( msg )
            elif level >= logging.WARNING:
                self.log_ctrl.WriteWarning( msg )
            elif level >= logging.INFO:
                self.log_ctrl.WriteInfo( msg )
            elif level >= logging.DEBUG:
                self.log_ctrl.WriteDebug( msg )
            else:
                self.log_ctrl.WriteError( msg )
        except Exception:
            self.handleError(record)

#--------------------------------------------------------------------------------
class StyledLogCtrl(wx.stc.StyledTextCtrl):
    'StyledLogCtrl'
    def __init__(self, app, parent):
        self.app = app

        wx.stc.StyledTextCtrl.__init__(self, parent)
        self.SetReadOnly( True )

        self.style_normal = 0
        self.style_error = 1
        self.style_info = 2
        self.style_warning = 3
        self.style_critical = 4
        self.style_debug = 4

        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)

        self.StyleSetSpec( wx.stc.STC_STYLE_DEFAULT, 
                "size:%d,face:%s,fore:#000000" % (wb_config.point_size, wb_config.face) )

        self.StyleSetSpec( self.style_normal,   "fore:#000000" )
        self.StyleSetSpec( self.style_error,    "fore:#DC143C" )    # Crimson
        self.StyleSetSpec( self.style_info,     "fore:#191970" )    # Midnight Blue
        self.StyleSetSpec( self.style_warning,  "fore:#008000" )    # Green
        self.StyleSetSpec( self.style_critical, "fore:#BA55D3" )    # Medium Orchid
        self.StyleSetSpec( self.style_debug,    "fore:#DC143C" )    # Crimson

        wx.EVT_KEY_DOWN( self, self.OnKeyDown )

    def OnKeyDown( self, event ):
        """
        Don't let the STC treat the TAB normally (insert a tab
        character.)  Turn it into a navigation event instead.
        """
        if event.GetKeyCode() == wx.WXK_TAB:
            flags = wx.NavigationKeyEvent.IsForward
            if event.ShiftDown():
                flags = wx.NavigationKeyEvent.IsBackward
            if event.ControlDown():
                flags |= wx.NavigationKeyEvent.WinChange
            self.Navigate(flags)            
        else:
            event.Skip()

    def SetWindowSize( self, size ):
        wx.stc.StyledTextCtrl.SetSize( self, size )
        self.EnsureCaretVisible()

    def WriteStyledText( self, text, style ):
        # only allowed to use GUI objects on the foreground thread
        if not self.app.isMainThread():
            self.app.foregroundProcess( self.WriteStyledText, (text, style) )
            return

        self.SetReadOnly(False)
        carot_pos = self.GetCurrentPos()
        insert_pos = self.GetLength()
        self.InsertText( insert_pos, text )
        self.StartStyling( insert_pos, 0xff )
        self.SetStyling( len(text), style )
        if carot_pos == insert_pos:
            new_carot_pos = self.GetLength()
            self.SetCurrentPos( new_carot_pos )
            self.SetSelectionStart( new_carot_pos )
            self.SetSelectionEnd( new_carot_pos )
            self.EnsureCaretVisible()
        self.SetReadOnly(True)

    def WriteNormal( self, text ):
        self.WriteStyledText( text, self.style_normal )

    def WriteError( self, text ):
        self.WriteStyledText( text, self.style_error )

    def WriteInfo( self, text ):
        self.WriteStyledText( text, self.style_info )

    def WriteWarning( self, text ):
        self.WriteStyledText( text, self.style_warning )

    def WriteCritical( self, text ):
        self.WriteStyledText( text, self.style_critical )

    def WriteDebug( self, text ):
        self.WriteStyledText( text, self.style_debug )

    def ClearText( self ):
        self.SetReadOnly(False)
        self.ClearAll()
        self.SetReadOnly( True )

class BookmarkMenu:
    def __init__( self, name ):
        self.name = name
        self.menu_items = []
        self.menu_folders = {}

        self.parent_menu = None
        self.all_menu_ids = []

    def add( self, path, pi ):
        if len(path) == 1:
            self.menu_items.append( (path[0], pi) )

        else:
            folder = path[0]
            if folder not in self.menu_folders:
                self.menu_folders[ folder ] = BookmarkMenu( folder )
                self.menu_items.append( (self.menu_folders[ folder ], None) )

            self.menu_folders[ folder ].add( path[1:], pi )

    def realise( self, parent_menu, frame ):
        self.parent_menu = parent_menu

        self.menu_items.sort( key=_keyMenuItem )

        for name_or_menu, pi in self.menu_items:
            if isinstance( name_or_menu, BookmarkMenu ):
                menu_id = wx.NewId()
                submenu = wx.Menu()

                self.all_menu_ids.append( menu_id )

                parent_menu.AppendMenu( menu_id, name_or_menu.name, submenu )
                name_or_menu.realise( submenu, frame )

            else:
                bm_id = wx.NewId()
                frame.all_bookmarks_id_to_pi[ bm_id ] = pi

                self.all_menu_ids.append( bm_id )

                parent_menu.Append( bm_id, pi.menu_name, pi.wc_path )
                try_wrapper = wb_exceptions.TryWrapperFactory( frame.app.log )
                wx.EVT_MENU( frame, bm_id, try_wrapper( frame.OnBookmarkGoto ) )

    def unrealise( self ):
        for name_or_menu, pi in self.menu_items:
            if isinstance( name_or_menu, BookmarkMenu ):
                name_or_menu.unrealise()

            else:
                # unrealise a bm item
                pass

        for menu_id in self.all_menu_ids:
            self.parent_menu.Delete( menu_id )
        
    def dump( self, indent ):
        prefix = ' '*indent
        for name, pi in self.menu_items:
            if isinstance( name, BookmarkMenu ):
                print '%s  Menu: %r' % (prefix, name)
                name.dump( indent + 4 )

            else:
                print '%s  Item: %r' % (prefix, name)

    def __repr__( self ):
        return '<Menu %s>' % self.name


def _keyMenuItem( item ):
    if isinstance( item[0], BookmarkMenu ):
        return item[0].name
    else:
        return item[0]
