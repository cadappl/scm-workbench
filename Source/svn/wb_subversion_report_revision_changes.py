'''
 ====================================================================
 Copyright (c) 2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_report_revision_changes.py

'''
import types
import wx

import pysvn

import wb_config
import wb_ids
import wb_images
import wb_exceptions
import wb_utils
import wb_list_panel_common
import wb_subversion_diff
import wb_subversion_utils
import wb_subversion_list_handler_common
import wb_platform_specific
import wb_subversion_annotate
import wb_subversion_info_dialog
import wb_subversion_history

class ReportRevisionChangesFrame(wx.Frame):
    def __init__( self, app, project_info, all_files, info1, info2 ):
        rev_info =  {'rev1': info1.revision.number
                    ,'rev2': info2.revision.number}
        wx.Frame.__init__( self, None, -1,
                            T_('Revision changes - r%(rev1)d vs. r%(rev2)d') %
                            rev_info,
                            size=(700,500) )

        self.app = app

        self.info1 = info1
        self.info2 = info2
        self.menu_text = T_('Diff r%(rev1)d vs. r%(rev2)d...') % rev_info

        self.menu_actions = wx.Menu()
        self.menu_actions.Append( wb_ids.id_SP_DiffRevisionRevision, self.menu_text, self.menu_text )

        self.menu_actions.AppendSeparator()
        self.menu_actions.Append( wb_ids.id_SP_Annotate, T_('Annotate...'), T_('Annotate...') )
        self.menu_actions.Append( wb_ids.id_SP_History, T_('Log history...'), T_('Log history...') )
        self.menu_actions.Append( wb_ids.id_SP_Info, T_('Information...'), T_('Information...') )

        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append( self.menu_actions, T_('&Actions') )

        self.SetMenuBar( self.menu_bar )

        # Add tool bar
        t = self.CreateToolBar( name="main",
                                style=wx.TB_HORIZONTAL )

        bitmap_size = (32,32)
        t.SetToolBitmapSize( bitmap_size )
        t.AddSimpleTool( wb_ids.id_SP_DiffRevisionRevision,
            wb_images.getBitmap( 'toolbar_images/diff.png', bitmap_size ),
            self.menu_text, self.menu_text )
        t.AddSimpleTool( wb_ids.id_SP_History,
            wb_images.getBitmap( 'toolbar_images/history.png', bitmap_size ),
            T_('Show History log'), T_('Show History log') )
        t.AddSimpleTool( wb_ids.id_SP_Info,
            wb_images.getBitmap( 'toolbar_images/info.png', bitmap_size ),
            T_('File Information'), T_('File Information') )
        t.Realize()

        try_wrapper = wb_exceptions.TryWrapperFactory( self.app.log )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        # create the individule panels
        self.panel_list = ReportRevisionChangesListPanel( app, self, self )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

        wx.EVT_BUTTON( self.panel_list, wx.ID_OK, self.app.eventWrapper( self.OnOk ) )

        self.project_info = ReportRevisionChangesProjectInfo( project_info, all_files )
        self.list_handler = ReportRevisionChangesListHandler( self.app, self.panel_list, self.project_info, self.menu_text )

        # draw the list - it updates the status info.
        self.panel_list.setHandler( self.list_handler )

        wx.EVT_MENU( self, wb_ids.id_SP_Annotate, self.app.eventWrapper( self.OnSpAnnotate ) )
        wx.EVT_MENU( self, wb_ids.id_SP_DiffRevisionRevision, self.app.eventWrapper( self.OnSpDiffRevisionRevision ) )
        wx.EVT_MENU( self, wb_ids.id_SP_History, self.app.eventWrapper( self.OnSpHistory ) )
        wx.EVT_MENU( self, wb_ids.id_SP_Info, self.app.eventWrapper( self.OnSpInfo ) )

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
        for filename, url in [(self.list_handler.getFilename( row ), self.list_handler.getUrl( row ))
                                for row in self.panel_list.getSelectedRows()]:
            self.app.setProgress( T_('Annotating %(count)d'), 0 )

            self.app.setAction( T_('Annotate %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                annotation = self.project_info.client_bg.annotate( url, peg_revision=self.info2.revision )
                ok = True
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

            h_frame = wb_subversion_annotate.AnnotateFrame( self.app, self.project_info, filename, annotation )
            h_frame.Show( True )

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )

    def OnSpDiffRevisionRevision( self, event ):
        for filename, url in [(self.list_handler.getFilename( row ), self.list_handler.getUrl( row ))
                                for row in self.panel_list.getSelectedRows()]:

            info1 = self.info1.copy()

            info1.peg_path = url
            info1.title = filename + '@r' + str(info1.revision.number)

            info2 = self.info2.copy()

            info2.peg_path = url
            info2.title = filename + '@r' + str(info2.revision.number)

            self.app.setAction( T_('Diff -r%(rev1)d:%(rev2)d %(url)s...') %
                                    {'rev1': info1.revision.number
                                    ,'rev2': info2.revision.number
                                    ,'url': url} )

            generator = wb_subversion_diff.subversionDiffFiles(
                                self.app,
                                self.project_info,
                                info1,
                                info2 )

            if type(generator) == types.GeneratorType:
                while True:
                    try:
                        where_to_go_next = generator.next()
                    except StopIteration:
                        # no problem all done
                        break

                    yield where_to_go_next

        self.app.setAction( T_('Ready') )

    def OnSpHistory( self, event ):
        dialog = wb_subversion_history.LogHistoryDialog( self.app, self.app.frame.tree_panel.tree_ctrl )
        result = dialog.ShowModal()
        if result != wx.ID_OK:
            return

        for filename, url in [(self.list_handler.getFilename( row ), self.list_handler.getUrl( row ))
                                for row in self.panel_list.getSelectedRows()]:
            self.app.setAction( 'Log history %s...' % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                file_url, history_entries = wb_subversion_history.getHistoryEntries(
                            self.project_info,
                            url,
                            dialog.getLimit(),
                            dialog.getRevisionEnd(),
                            dialog.getIncludeTags() )
                ok = True
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

            h_frame = wb_subversion_history.HistoryFileFrame(
                        self.app,
                        self.project_info,
                        filename,
                        url,
                        history_entries )
            h_frame.Show( True )

        self.app.setAction( T_('Ready') )

    def OnSpInfo( self, event ):
        for filename, url in [(self.list_handler.getFilename( row ), self.list_handler.getUrl( row ))
                                for row in self.panel_list.getSelectedRows()]:
            try:
                entry = self.project_info.client_fg.info2( url, peg_revision=self.info2.revision, recurse=False )

                dialog = wb_subversion_info_dialog.InfoDialog(
                        self.app,
                        self.panel_list,
                        filename,
                        entry )
                dialog.ShowModal()

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

class ReportRevisionChangesListHandler(wb_subversion_list_handler_common.SubversionListHandlerCommon):
    def __init__( self, app, parent, project_info, menu_text ):
        wb_subversion_list_handler_common.SubversionListHandlerCommon.__init__( self, app, parent, project_info )

        self.all_excluded_files = {}
        self.menu_text = menu_text

    def _getNameColPrefix( self ):
        return 0

    # use the repos status in the report
    def getTextStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_text_status

    # use the repos status in the report
    def getPropStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.repos_prop_status

    def statusFormatString( self, file ):
        text_code = wb_subversion_utils.wc_status_kind_map[ file.text_status ]
        prop_code = wb_subversion_utils.wc_status_kind_map[ file.prop_status ]
        if text_code == ' ' and prop_code != ' ':
            text_code = '_'

        return file.get('branch_text_states', '') + text_code + prop_code

    def setupColumnInfo( self ):
        self.column_info.setFrom( [T_('State'), T_('Name')], [5, 100] )

    def statusColour( self, file ):
        # show that a file is on the exclude list
        if file.path in self.getAllGreyFilenames():
            return wb_config.colour_status_disabled
        else:
            return wb_config.colour_status_normal

    def getContextMenu( self ):
        menu_template = \
            [('', wb_ids.id_SP_DiffRevisionRevision, self.menu_text )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Annotate, T_('Annotate...') )
            ,('', wb_ids.id_SP_History, T_('Log history...') )
            ,('', wb_ids.id_SP_Info, T_('Information...') )
            ]
        return wb_utils.populateMenu( wx.Menu(), menu_template )

    def getAllGreyFilenames( self ):
        # show all excluded files in grey
        return self.all_excluded_files

class ReportRevisionChangesProjectInfo:
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

class ReportRevisionChangesListPanel(wb_list_panel_common.WbListPanelCommon):
    def __init__( self, app, frame, parent ):
        wb_list_panel_common.WbListPanelCommon.__init__( self, app, frame, parent )

    def addToSizer( self, v_sizer ):
        pass

    def getAcceleratorTableInit( self ):
        if wx.Platform == '__WXMAC__':
            acc_init =[
                (wx.ACCEL_ALT, ord('D'), wb_ids.id_SP_DiffRevisionRevision),
                (wx.ACCEL_ALT, ord('L'), wb_ids.id_SP_History),
                ]
        elif wx.Platform == '__WXMSW__':
            acc_init =[
                (wx.ACCEL_CTRL, ord('D'), wb_ids.id_SP_DiffRevisionRevision),
                (wx.ACCEL_CTRL, ord('L'), wb_ids.id_SP_History),
                ]
        else:
            # Unix
            acc_init =[
                (wx.ACCEL_CTRL, ord('D'), wb_ids.id_SP_DiffWorkBase),
                (wx.ACCEL_CTRL, ord('L'), wb_ids.id_SP_History),
                ]

        return acc_init
