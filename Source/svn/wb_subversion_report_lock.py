'''
 ====================================================================
 Copyright (c) 2006-2011 Barry A Scott.  All rights reserved.
 Copyright (c) 2010-2012 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_report_lock.py

'''
import wx
import sys
import wb_images
import time
import pysvn

import wb_config
import wb_ids
import wb_images
import wb_exceptions
import wb_list_panel_common
import wb_utils
import wb_subversion_utils
import wb_subversion_list_handler_common
import wb_platform_specific

class ReportLockFrame(wx.Frame):
    def __init__( self, app, project_info, all_files, show_repos_locks=False ):
        if show_repos_locks:
            title = T_("Repository Lock Report")
        else:
            title = T_("Working Copy Lock Report")
        wx.Frame.__init__( self, None, -1, title, size=(700,500) )

        self.app = app

        self.menu_actions = wx.Menu()
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...'), T_('Diff WC vs. HEAD...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...'), T_('Diff WC vs. branch origin BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...'), T_('Diff WC vs. branch origin HEAD...') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Annotate, T_('Annotate...'), T_('Annotate...') )
        self.menu_actions.Append( wb_ids.id_SP_History, T_('Log history...'), T_('Log history...') )
        self.menu_actions.Append( wb_ids.id_SP_Info, T_('Information...'), T_('Information...') )

        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append( self.menu_actions, T_("&Actions") )

        self.SetMenuBar( self.menu_bar )

        # Add tool bar
        t = self.CreateToolBar( name="main",
                                style=wx.TB_HORIZONTAL )

        bitmap_size = (32,32)
        t.SetToolBitmapSize( bitmap_size )
        t.AddSimpleTool( wb_ids.id_SP_DiffWorkHead,
            wb_images.getBitmap( 'toolbar_images/diff.png', bitmap_size ),
            T_('Diff changes against HEAD'), T_('Diff changes against HEAD') )
        t.AddSimpleTool( wb_ids.id_SP_History,
            wb_images.getBitmap( 'toolbar_images/history.png', bitmap_size ),
            T_('Show History log'), T_('Show History log') )
        t.AddSimpleTool( wb_ids.id_SP_Info,
            wb_images.getBitmap( 'toolbar_images/info.png', bitmap_size ),
            T_('File Information'), T_('File Information') )
        t.AddSeparator()
        t.AddSimpleTool( wb_ids.id_SP_Lock,
            wb_images.getBitmap( 'toolbar_images/lock.png', bitmap_size ),
            T_('Lock File'), T_('Lock File') )
        t.AddSimpleTool( wb_ids.id_SP_Unlock,
            wb_images.getBitmap( 'toolbar_images/unlock.png', bitmap_size ),
            T_('Unlock File'), T_('Unlock File') )
        t.Realize()

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        # create the individule panels
        self.panel_list = ReportLockListPanel( app, self, self, show_repos_locks )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

        wx.EVT_BUTTON( self.panel_list, wx.ID_OK, self.app.eventWrapper( self.OnOk ) )

        self.project_info = ReportLockProjectInfo( project_info, all_files )
        self.list_handler = ReportLockListHandler( self.app, self.panel_list, self.project_info, show_repos_locks )

        # draw the list - its Lock the status info
        self.panel_list.setHandler( self.list_handler )

        wx.EVT_MENU( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnSpAnnotate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkHead, self.app.eventWrapper( self.OnSpDiffWorkHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginBase, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginHead, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnSpHistory ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Info, self.app.eventWrapper( self.OnSpInfo ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Lock, self.app.eventWrapper( self.OnSpLock ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Unlock, self.app.eventWrapper( self.OnSpUnlock ) )

    def clearUpdateUiState( self ):
        pass

    def getUpdateUiState( self ):
        pass

    def setEventHandler( self, handler ):
        self.handler = handler

    def OnCloseWindow( self, event ):
        self.Destroy()

    def OnCancel( self, event ):
        self.Destroy()

    def OnOk( self, event ):
        self.Destroy()

    # command events
    def OnSpAnnotate( self, event ):
        return self.panel_list.OnSpAnnotate()

    def OnSpDiffWorkHead( self, event ):
        return self.panel_list.OnSpDiffWorkHead()

    def OnSpDiffWorkBranchOriginBase( self, event ):
        return self.panel_list.OnSpDiffWorkBranchOriginBase()
        
    def OnSpDiffWorkBranchOriginHead( self, event ):
        return self.panel_list.OnSpDiffWorkBranchOriginHead()

    def OnSpHistory( self, event ):
        return self.panel_list.OnSpHistory()

    def OnSpInfo( self, event ):
        return self.panel_list.OnSpInfo()

    def OnSpLock( self, event ):
        return self.panel_list.OnSpLock()

    def OnSpUnlock( self, event ):
        return self.panel_list.OnSpUnlock()

class ReportLockListHandler(wb_subversion_list_handler_common.SubversionListHandlerCommon):
    def __init__( self, app, parent, project_info, show_repos_locks ):
        wb_subversion_list_handler_common.SubversionListHandlerCommon.__init__( self, app, parent, project_info )
        self.show_repos_locks = show_repos_locks

        self.all_excluded_files = {}

    # use the repos status in the report
    def getTextStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_text_status

    # use the repos status in the report
    def getPropStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_prop_status

    def statusFormatString( self, status ):
        text_code = wb_subversion_utils.wc_status_kind_map[ status.repos_text_status ]
        prop_code = wb_subversion_utils.wc_status_kind_map[ status.repos_prop_status ]
        if text_code == ' ':
            text_code = '_'
        if prop_code != ' ':
            prop_code = '_'

        wc_lock = ' '
        if status.entry is not None and status.entry.lock_token is not None:
            wc_lock = 'K'
        repos_lock = ' '
        if status.repos_lock is not None:
            repos_lock = 'O'
            if wc_lock == ' ':
                wc_lock = '_'

        return '%s%s%s%s' % (text_code, prop_code, wc_lock, repos_lock)

    def setupColumnInfo( self ):
        self.column_info.setFrom( [ T_('State'), T_('Name'), T_('Lock Owner'), T_('Lock Comment') ], [5, 40, 10, 60] )

    def statusColour( self, file ):
        # show that a file is on the exclude list
        if file.path in self.getAllGreyFilenames():
            return wb_config.colour_status_disabled
        else:
            return wb_config.colour_status_normal

    def getContextMenu( self ):
        menu_template = \
            [('', wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...') )
            ,('', wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...') )
            ,('', wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Annotate, T_('Annotate...') )
            ,('', wb_ids.id_SP_History, T_('Log history...') )
            ,('', wb_ids.id_SP_Info, T_('Information...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Lock, T_('Lock...') )
            ,('', wb_ids.id_SP_Unlock, T_('Unlock...') )
            ]
        return wb_utils.populateMenu( wx.Menu(), menu_template )

    def getAllGreyFilenames( self ):
        # show all excluded files in grey
        return self.all_excluded_files

    def getReportLockFiles( self ):
        return [entry.path for entry in self.project_info.all_files
                if entry.path not in self.all_excluded_files]

class ReportLockProjectInfo:
    def __init__( self, project_info, all_files ):
        self.all_files = all_files
        self.need_properties = False
        self.project_name = project_info.project_name
        self.url = project_info.url
        self.wc_path = project_info.wc_path
        self.need_checkout = False
        self.need_upgrade = False

        self.client_fg = project_info.client_fg
        self.client_bg = project_info.client_bg

    def getTagsUrl( self, rel_url ):
        return None

    def setNeedProperties( self, need_properties ):
        self.need_properties = need_properties

    def updateStatus( self ):
        pass

    def getFilesStatus( self ):
        return self.all_files

    def getProperty( self, filename, prop_name ):
        return ''

    def getWorkingDir( self ):
        return self.wc_path

class ReportLockListPanel(wb_list_panel_common.WbListPanelCommon):
    def __init__( self, app, frame, parent, show_repos_locks ):
        wb_list_panel_common.WbListPanelCommon.__init__( self, app, frame, parent )
        self.show_repos_locks = show_repos_locks

    def addToSizer( self, v_sizer ):
        pass

    def getAcceleratorTableInit( self ):
        acc_init =[
                (wx.ACCEL_CMD, ord('D'), wb_ids.id_SP_DiffWorkHead),
                (wx.ACCEL_CMD, ord('L'), wb_ids.id_SP_History),
                ]
        return acc_init
