'''
 ====================================================================
 Copyright (c) 2006-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_checkin.py

'''
import wx
import sys
import wb_images
import time
import pysvn

import wb_ids
import wb_images
import wb_exceptions
import wb_list_panel_common
import wb_utils
import wb_subversion_utils
import wb_subversion_list_handler_common
import wb_platform_specific
import wb_dialogs

id_exclude = wx.NewId()
id_include = wx.NewId()

class CheckinFrame(wx.Frame):
    def __init__( self, app, project_info, all_files ):
        wx.Frame.__init__( self, None, -1, T_('Check in for %s') % project_info.wc_path, size=(700,500) )

        self.app = app

        self.menu_actions = wx.Menu()
        self.menu_actions.Append(  wb_ids.id_File_Edit, T_('Edit'), T_('Edit') )
        if wx.Platform in ['__WXMSW__','__WXMAC__']:
            self.menu_actions.Append(  wb_ids.id_Shell_Open, T_('Open'), T_('Open') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBase, T_('Diff WC vs. BASE...'), T_('Diff WC vs. BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...'), T_('Diff WC vs. HEAD...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...'), T_('Diff WC vs. branch origin BASE...') )
        self.menu_actions.Append(  wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...'), T_('Diff WC vs. branch origin HEAD...') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Annotate, T_('Annotate...'), T_('Annotate...') )
        self.menu_actions.Append( wb_ids.id_SP_History, T_('Log history...'), T_('Log history...') )
        self.menu_actions.Append( wb_ids.id_SP_Info, T_('Information...'), T_('Information...') )
        self.menu_actions.Append( wb_ids.id_SP_Properties, T_('Properties...'), T_('Properties...') )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SelectAll, T_('Select All'), T_('Select All') )
        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( id_exclude, T_('Exclude...'), T_('Exclude from check in') )
        self.menu_actions.Append( id_include, T_('Include...'), T_('Include from check in') )

        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append( self.menu_actions, T_('&Actions') )

        self.SetMenuBar( self.menu_bar )

        # Add tool bar
        t = self.CreateToolBar( name='main',
                                style=wx.TB_HORIZONTAL ) # | wx.NO_BORDER | wx.TB_TEXT )

        bitmap_size = (32,32)
        t.SetToolBitmapSize( bitmap_size )
        t.AddSimpleTool( wb_ids.id_File_Edit,
            wb_images.getBitmap( 'toolbar_images/edit.png', bitmap_size ),
            T_('Edit File'), T_('Edit File') )
        if wx.Platform in ['__WXMSW__','__WXMAC__']:
            t.AddSimpleTool( wb_ids.id_Shell_Open,
                wb_images.getBitmap( 'toolbar_images/open.png', bitmap_size ),
                T_('Open File'), T_('Open File') )
        t.AddSeparator()
        t.AddSimpleTool( wb_ids.id_SP_DiffWorkBase,
            wb_images.getBitmap( 'toolbar_images/diff.png', bitmap_size ),
            T_('Diff changes against base'), T_('Diff changes against base') )
        t.AddSimpleTool( wb_ids.id_SP_History,
            wb_images.getBitmap( 'toolbar_images/history.png', bitmap_size ),
            T_('Show History log'), T_('Show History log') )
        t.AddSimpleTool( wb_ids.id_SP_Info,
            wb_images.getBitmap( 'toolbar_images/info.png', bitmap_size ),
            T_('File Information'), T_('File Information') )
        t.AddSimpleTool( wb_ids.id_SP_Properties,
            wb_images.getBitmap( 'toolbar_images/property.png', bitmap_size ),
            T_('File Properties'), T_('File Properties') )
        t.AddSeparator()
        t.AddSimpleTool( wb_ids.id_SP_Revert,
            wb_images.getBitmap( 'toolbar_images/revert.png', bitmap_size ),
            T_('Revert'), T_('Revert selected Files and Folders') )
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

        self.message_filename = wb_platform_specific.getLastCheckinMessageFilename()
        self.last_log_message_text = None

        try:
            f = file( self.message_filename, 'r' )
            self.last_log_message_text = f.read().decode('utf-8').strip()
            f.close()
        except EnvironmentError:
            self.last_log_message_text = ''

        # Create the splitter windows
        self.splitter = wx.SplitterWindow( self, -1 )

        # Make sure the splitters can't be removed by setting a minimum size
        self.splitter.SetMinimumPaneSize( 100 )   # list, log

        # create the individule panels
        self.panel_list = CheckinListPanel( app, self, self.splitter )

        # Create the log message panel
        self.panel_log = wx.Panel( self.splitter, -1 )
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.label_ctrl = wx.StaticText( self.panel_log, -1, T_('Log message'), style=wx.ALIGN_LEFT )
        self.log_message_ctrl = wx.TextCtrl( self.panel_log, -1, style=wx.TE_MULTILINE )

        self.button_ok = wx.Button( self.panel_log, wx.ID_OK, T_(' Check In ') )
        self.button_cancel = wx.Button( self.panel_log, wx.ID_CANCEL, T_(' Cancel ') )
        self.button_ok.SetDefault()

        self.button_last_log_message = wx.Button( self.panel_log, -1, T_('Insert Last Message') )
        self.button_last_log_message.Enable( len(self.last_log_message_text) > 0 )
        self.h_sizer.Add( self.button_last_log_message )

        self.button_ok.Enable( False )

        wx.EVT_BUTTON( self.panel_log, self.button_last_log_message.GetId(), try_wrapper( self.OnInsertLastLogMessage ) )
        wx.EVT_TEXT( self.panel_log, self.log_message_ctrl.GetId(), try_wrapper( self.OnLogMessageChanged ) )

        self.h_sizer.Add( (60, 20), 1, wx.EXPAND)
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15)
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.label_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.log_message_ctrl, 1, wx.EXPAND|wx.ALL, 5 )

        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        self.splitter.SplitHorizontally( self.panel_list, self.panel_log, -150 )

        self.panel_log.SetAutoLayout( True )
        self.panel_log.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self.panel_log )
        self.panel_log.Layout()

        wx.EVT_CLOSE( self, self.OnCloseWindow )

        wx.EVT_BUTTON( self.panel_log, wx.ID_OK, self.app.eventWrapper( self.OnOk ) )
        wx.EVT_BUTTON( self.panel_log, wx.ID_CANCEL, try_wrapper( self.OnCancel ) )

        self.project_info = CheckinProjectInfo( project_info, all_files )
        self.list_handler = CheckinListHandler( self.app, self.panel_list, self.project_info )

        # draw the list - its updates the status info
        self.panel_list.setHandler( self.list_handler )

        wx.EVT_MENU( self, wb_ids.id_File_Edit, try_wrapper( self.OnFileEdit ) )
        wx.EVT_MENU( self, wb_ids.id_Shell_Open, try_wrapper( self.OnShellOpen ) )

        wx.EVT_MENU( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnSpAnnotate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBase, self.app.eventWrapper( self.OnSpDiffWorkBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkHead, self.app.eventWrapper( self.OnSpDiffWorkHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginBase, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginBase ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffWorkBranchOriginHead, self.app.eventWrapper( self.OnSpDiffWorkBranchOriginHead ) )
        wx.EVT_MENU( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnSpHistory ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Info, self.app.eventWrapper( self.OnSpInfo ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Properties, self.app.eventWrapper( self.OnSpProperties ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Revert, self.app.eventWrapper( self.OnSpRevert) )

        wx.EVT_MENU( self, wb_ids.id_SelectAll, self.app.eventWrapper( self.OnSelectAll ) )

        wx.EVT_MENU( self, id_exclude, self.app.eventWrapper( self.OnExcludeItem ) )
        wx.EVT_MENU( self, id_include, self.app.eventWrapper( self.OnIncludeItem ) )

        self.log_message_ctrl.SetFocus()

    def OnSelectAll( self, event ):
        self.panel_list.selectAll()
        print self.panel_list.getSelectedRows()

    def OnExcludeItem( self, event ):
        self.list_handler.Cmd_Checkin_ExcludeItem( self.panel_list.getSelectedRows() )
        self.panel_list.drawList()

    def OnIncludeItem( self, event ):
        self.list_handler.Cmd_Checkin_IncludeItem( self.panel_list.getSelectedRows() )
        self.panel_list.drawList()

    def clearUpdateUiState( self ):
        pass

    def getUpdateUiState( self ):
        pass

    def setEventHandler( self, handler ):
        self.handler = handler

    def OnInsertLastLogMessage( self, event ):
        self.log_message_ctrl.WriteText( self.last_log_message_text )
        self.button_ok.Enable( True )

    def OnLogMessageChanged( self, event ):
        self.button_ok.Enable( len( self.log_message_ctrl.GetValue().strip() ) > 0 )

    def OnCloseWindow( self, event ):
        self.Destroy()

    def OnCancel( self, event ):
        self.Destroy()

    def OnOk( self, event ):
        self.Hide()

        message = self.log_message_ctrl.GetValue().encode('utf-8')
        try:
            f = file( self.message_filename, 'w' )
            f.write( message )
            f.close()
        except EnvironmentError:
            pass

        all_filenames = self.list_handler.getCheckinFiles()
        self.app.setAction( T_('Check in %s...') % self.project_info.wc_path )
        self.app.setProgress( T_('Sent %(count)d of %(total)d'), len( all_filenames ) )

        yield self.app.backgroundProcess

        ok = False
        try:
            commit_info = self.project_info.client_bg.checkin( all_filenames, message )
            ok = True
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        self.app.refreshFrame()
        self.app.setAction( T_('Ready') )
        self.app.clearProgress()

        self.Destroy()

        if ok:
            rev = commit_info['revision']
            if rev:
                self.app.log.info( T_('Checkin created revision %d') % rev.number )
            else:
                self.app.log.warning( T_('No changes to checkin ') )

            post_commit_err = commit_info['post_commit_err']
            if post_commit_err is not None:
                self.app.log.error( post_commit_err )
                wx.MessageBox( post_commit_err, (T_('Post commit error')),
                                style=wx.OK|wx.ICON_ERROR )

    # command events
    def OnFileEdit( self, event ):
        return self.panel_list.OnFileEdit()

    def OnShellOpen( self, event ):
        return self.panel_list.OnShellOpen()

    def OnSpAnnotate( self, event ):
        return self.panel_list.OnSpAnnotate()

    def OnSpDiffWorkBase( self, event ):
        return self.panel_list.OnSpDiffWorkBase()

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

    def OnSpProperties( self, event ):
        return self.panel_list.OnSpProperties()

    def OnSpRevert( self, event ):
        self.Hide()
        # Invoke the revert handler
        result = self.panel_list.OnSpRevert()

        # If all files have been reverted, don't show the checkin box.
        if len(self.project_info.all_files) == 0:
            wx.MessageBox( T_('There are no changes to check in'),
                T_('Warning'), style=wx.OK|wx.ICON_EXCLAMATION )
            self.Destroy()
        else:
            # Redraw the panel
            self.panel_list.drawList()
            self.Show()

        # update the main frame
        self.app.refreshFrame()

        return result

class CheckinListHandler(wb_subversion_list_handler_common.SubversionListHandlerCommon):
    def __init__( self, app, parent, project_info ):
        wb_subversion_list_handler_common.SubversionListHandlerCommon.__init__( self, app, parent, project_info )

        self.all_excluded_files = {}
        self.__parent = parent

    def getContextMenu( self ):
        menu_template = [
            ('', wb_ids.id_File_Edit, T_('Edit') )
            ]
        if wx.Platform in ['__WXMSW__','__WXMAC__']:
            menu_template += [
                ('', wb_ids.id_Shell_Open, T_('Open') )
                ]
        menu_template += [
            ('-', 0, 0 ),
            ('', wb_ids.id_SP_DiffWorkBase, T_('Diff WC vs. BASE...') ),
            ('', wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...') ),
            ('', wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...') ),
            ('', wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...') ),
            ('-', 0, 0 ),
            ('', wb_ids.id_SP_Annotate, T_('Annotate...') ),
            ('', wb_ids.id_SP_History, T_('Log history...') ),
            ('', wb_ids.id_SP_Info, T_('Information...') ),
            ('', wb_ids.id_SP_Properties, T_('Properties...') ),
            ('', wb_ids.id_SP_Revert, T_('Revert...') ),
            ]

        return wb_utils.populateMenu( wx.Menu(), menu_template )

    def Cmd_Checkin_ExcludeItem( self, all_rows ):
        #print 'Cmd_Checkin_ExcludeItem',all_rows
        for row in all_rows:
            self.all_excluded_files[ self.getFilename( row ) ] = None

    def Cmd_Checkin_IncludeItem( self, all_rows ):
        #print 'Cmd_Checkin_IncludeItem',all_rows
        for row in all_rows:
            if self.getFilename( row ) in self.all_excluded_files:
                del self.all_excluded_files[ self.getFilename( row ) ]

    def getAllGreyFilenames( self ):
        # show all excluded files in grey
        return self.all_excluded_files

    def getCheckinFiles( self ):
        return [entry.path for entry in self.project_info.all_files
                if entry.path not in self.all_excluded_files]

    def Cmd_File_Revert( self, all_rows ):
        # Pop up a confirm dialog box.
        dialog = wb_dialogs.ConfirmAction( self.__parent, T_('Revert'), self.getStatusAndFilenames( all_rows ) )
        result = dialog.ShowModal()
        if result != wx.ID_OK:
            return

        try:
            #Revert each file
            for filename in [self.getFilename( row ) for row in all_rows]:
                self.project_info.client_fg.revert( filename )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

         # Build up a list of files that are still dirty.
        all_files = self.project_info.client_bg.status(
            self.project_info.wc_path,
            recurse=True, get_all=False,
            ignore=True, update=False )
        all_files = [entry for entry in all_files
                        if wb_subversion_utils.wc_status_checkin_map[ entry.text_status ]
                        or wb_subversion_utils.wc_status_checkin_map[ entry.prop_status ]]

        # Set the project files to be this new list
        self.project_info.all_files = all_files

class CheckinProjectInfo:
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

class CheckinListPanel(wb_list_panel_common.WbListPanelCommon):
    def __init__( self, app, frame, parent ):
        wb_list_panel_common.WbListPanelCommon.__init__( self, app, frame, parent )

    def getAcceleratorTableInit( self ):
        acc_init =[
                (wx.ACCEL_CMD, ord('D'), wb_ids.id_SP_DiffWorkBase),
                (wx.ACCEL_CMD, ord('E'), wb_ids.id_File_Edit),
                (wx.ACCEL_CMD, ord('L'), wb_ids.id_SP_History),
                (wx.ACCEL_CMD, ord('I'), wb_ids.id_SP_Info),
                (wx.ACCEL_CMD, ord('P'), wb_ids.id_SP_Properties),
                (wx.ACCEL_CMD, ord('O'), wb_ids.id_Shell_Open),
                ]
        return acc_init
