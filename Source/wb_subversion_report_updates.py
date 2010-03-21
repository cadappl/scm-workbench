'''
 ====================================================================
 Copyright (c) 2006-2007 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_report_updates.py

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
import wb_subversion_utils
import wb_subversion_list_handler_common
import wb_platform_specific

id_exclude = wx.NewId()
id_include = wx.NewId()

class ReportUpdatesFrame(wx.Frame):
    def __init__( self, app, project_info, all_files ):
        wx.Frame.__init__( self, None, -1, T_("Updates Report"), size=(700,500) )

        self.app = app

        self.menu_actions = wx.Menu()
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...'), T_('Diff WC vs. HEAD...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...'), T_('Diff WC vs. branch origin BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...'), T_('Diff WC vs. branch origin HEAD...') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Annotate, T_('Annotate...'), T_('Annotate...') )
        self.menu_actions.Append( wb_ids.id_SP_History, T_('Log history...'), T_('Log history...') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( id_exclude, T_('Exclude...'), T_('Exclude from update') )
        self.menu_actions.Append( id_include, T_('Include...'), T_('Include in update') )

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
        t.AddSeparator()
        t.AddSimpleTool( id_exclude,
            wb_images.getBitmap( 'toolbar_images/exclude.png', bitmap_size ),
            T_('Exclude from check in'), T_('Exclude from check in') )
        t.AddSimpleTool( id_include,
            wb_images.getBitmap( 'toolbar_images/include.png', bitmap_size ),
            T_('Include in check in'), T_('Include in check in') )
        t.Realize()

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        # create the individule panels
        self.panel_list = ReportUpdatesListPanel( app, self, self )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

        wx.EVT_BUTTON( self.panel_list, wx.ID_OK, self.app.eventWrapper( self.OnOk ) )
        wx.EVT_BUTTON( self.panel_list, wx.ID_CANCEL, try_wrapper( self.OnCancel ) )

        self.project_info = ReportUpdatesProjectInfo( project_info, all_files )
        self.list_handler = ReportUpdatesListHandler( self.app, self.panel_list, self.project_info )

        # draw the list - its updates the status info
        self.panel_list.setHandler( self.list_handler )

        wx.EVT_MENU( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnSpAnnotate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkHead, self.app.eventWrapper( self.OnSpDiffWorkHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginBase, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginHead, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnSpHistory ) )

        wx.EVT_MENU( self, id_exclude, self.app.eventWrapper( self.OnExcludeItem ) )
        wx.EVT_MENU( self, id_include, self.app.eventWrapper( self.OnIncludeItem ) )

    def OnExcludeItem( self, event ):
        self.list_handler.Cmd_ReportUpdates_ExcludeItem( self.panel_list.getSelectedRows() )
        self.panel_list.drawList()

    def OnIncludeItem( self, event ):
        self.list_handler.Cmd_ReportUpdates_IncludeItem( self.panel_list.getSelectedRows() )
        self.panel_list.drawList()

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
        self.Hide()

        all_filenames = self.list_handler.getReportUpdatesFiles()
        self.app.setAction( T_('Update %s...') % self.project_info.wc_path )
        self.app.setProgress( T_('Updated %(count)d'), 0 )

        yield self.app.backgroundProcess

        try:
            for filename in all_filenames:
                rev_list = self.project_info.client_bg.update( filename, recurse=False )
                for rev in rev_list:
                    if rev.number > 0:
                        count = self.app.getProgressValue( 'count' )
                        if count == 0:
                            self.app.log.info( T_('Updated %(filename)s to revision %(rev)d, no new updates') %
                                                {'filename': filename
                                                ,'rev': rev.number} )
                        else:
                            self.app.log.info( S_('Updated %(filename)s to revision %(rev)d, %(count)d new update', 
                                                  'Updated %(filename)s to revision %(rev)d, %(count)d new updates', count) %
                                                {'filename': filename
                                                ,'rev': rev.number
                                                ,'count': count} )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

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

class ReportUpdatesListHandler(wb_subversion_list_handler_common.SubversionListHandlerCommon):
    def __init__( self, app, parent, project_info ):
        wb_subversion_list_handler_common.SubversionListHandlerCommon.__init__( self, app, parent, project_info )

        self.all_excluded_files = {}

    # use the repos status in the report
    def getTextStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_text_status

    # use the repos status in the report
    def getPropStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_prop_status

    def statusFormatString( self, file ):
        text_code = wb_subversion_utils.wc_status_kind_map[ file.repos_text_status ]
        prop_code = wb_subversion_utils.wc_status_kind_map[ file.repos_prop_status ]
        if text_code == ' ' and prop_code != ' ':
            text_code = '_'

        return '%s%s' % (text_code, prop_code)

    def setupColumnInfo( self ):
        self.column_info.setFrom( [ T_('State'), T_('Name') ], [5, 100] )

    def statusColour( self, file ):
        # show that a file is on the exclude list
        if file.path in self.getAllGreyFilenames():
            return wb_config.colour_status_disabled
        else:
            return wb_config.colour_status_normal

    def getContextMenu( self ):
        menu_template = \
            [('', wb_ids.id_File_Edit, T_('Edit') )]
        if wx.Platform in ['__WXMSW__','__WXMAC__']:
            menu_template += \
                [('', wb_ids.id_Shell_Open, T_('Open') )]
        menu_template += \
            [('-', 0, 0 )
            ,('', wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...') )
            ,('', wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...') )
            ,('', wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Annotate, T_('Annotate...') )
            ,('', wb_ids.id_SP_History, T_('Log history...') )
            ]

        return wb_subversion_utils.populateMenu( wx.Menu(), menu_template )

    def Cmd_ReportUpdates_ExcludeItem( self, all_rows ):
        for row in all_rows:
            self.all_excluded_files[ self.getFilename( row ) ] = None

    def Cmd_ReportUpdates_IncludeItem( self, all_rows ):
        for row in all_rows:
            if self.getFilename( row ) in self.all_excluded_files:
                del self.all_excluded_files[ self.getFilename( row ) ]

    def getAllGreyFilenames( self ):
        # show all excluded files in grey
        return self.all_excluded_files

    def getReportUpdatesFiles( self ):
        return [entry.path for entry in self.project_info.all_files
                if entry.path not in self.all_excluded_files]

class ReportUpdatesProjectInfo:
    def __init__( self, project_info, all_files ):
        self.all_files = all_files
        self.need_properties = False
        self.project_name = project_info.project_name
        self.url = project_info.url
        self.wc_path = project_info.wc_path
        self.need_checkout = False

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

class ReportUpdatesListPanel(wb_list_panel_common.WbListPanelCommon):
    def __init__( self, app, frame, parent ):
        wb_list_panel_common.WbListPanelCommon.__init__( self, app, frame, parent )

    def addToSizer( self, v_sizer ):
        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(" Update ") )
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(" Cancel ") )
        self.button_ok.SetDefault()

        self.button_ok.Enable( True )

        self.h_sizer.Add( (60, 20), 1, wx.EXPAND)
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15)
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

    def getAcceleratorTableInit( self ):
        acc_init =[
                (wx.ACCEL_CMD, ord('D'), wb_ids.id_SP_DiffWorkHead),
                (wx.ACCEL_CMD, ord('L'), wb_ids.id_SP_History),
                ]
        return acc_init
