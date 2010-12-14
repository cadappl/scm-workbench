'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_list_handler.py

'''
import sys
import os

import pysvn
import wx

import wb_ids
import wb_subversion_list_handler_common
import wb_subversion_info_dialog
import wb_subversion_properties_dialog
import wb_subversion_utils
import wb_subversion_checkin
import wb_clipboard
import wb_diff_frame
import wb_dialogs

class SubversionListHandler(wb_subversion_list_handler_common.SubversionListHandlerCommon):
    def __init__( self, app, list_panel, project_info ):
        wb_subversion_list_handler_common.SubversionListHandlerCommon.__init__( self, app, list_panel, project_info )

    def __repr__( self ):
        return '<SubversionListHandler %r>' % self.project_info

    def getContextMenu( self ):
        if self.project_info.need_checkout:
            menu_template = \
                [('', wb_ids.id_SP_Checkout, T_('Checkout') )]
        else:
            menu_template = \
                [('', wb_ids.id_File_Edit, T_('Edit') )]
            if wx.Platform in ['__WXMSW__','__WXMAC__']:
                menu_template += \
                    [('', wb_ids.id_Shell_Open, T_('Open') )]
            menu_template += \
                [('-', 0, 0 )
                ,('', wb_ids.id_SP_DiffWorkBase, T_('Diff WC vs. BASE...') )
                ,('', wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...') )
                ,('', wb_ids.id_SP_DiffWorkBranchOriginBase, T_('Diff WC vs. branch origin BASE...') )
                ,('', wb_ids.id_SP_DiffWorkBranchOriginHead, T_('Diff WC vs. branch origin HEAD...') )
                ,('>', wb_ids.id_SP_ConflictMenu, T_('Conflict'),
                    [('', wb_ids.id_SP_DiffOldMine, T_('Diff Conflict Old vs. Mine...') )
                    ,('', wb_ids.id_SP_DiffMineNew, T_('Diff Conflict Mine vs. New...') )
                    ,('', wb_ids.id_SP_DiffOldNew, T_('Diff Conflict Old vs. New...') )
                    ,('-', 0, 0 )
                    ,('', wb_ids.id_SP_Resolved, T_('Resolved Conflict') )
                    ])
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Annotate, T_('Annotate...') )
                ,('', wb_ids.id_SP_History, T_('Log history...') )
                ,('', wb_ids.id_SP_Info, T_('Information...') )
                ,('', wb_ids.id_SP_Properties, T_('Properties...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Lock, T_('Lock...') )
                ,('', wb_ids.id_SP_Unlock, T_('Unlock...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Switch, T_('Switch...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Update, T_('Update') )
                ,('', wb_ids.id_SP_UpdateTo, T_('Update to..') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Checkin, T_('Checkin...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Add, T_('Add') )
                ,('', wb_ids.id_SP_Rename, T_('Rename...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Delete, T_('Delete...') )
                ,('', wb_ids.id_SP_Revert, T_('Revert...') )
                ,('-', 0, 0 )
                ,('', wb_ids.id_SP_Cleanup, T_('Clean up') )
                ]
        menu_template += wb_subversion_utils.handleMenuInfo( self.project_info )

        return wb_subversion_utils.populateMenu( wx.Menu(), menu_template )

    def getAllGreyFilenames( self ):
        # show files on the clipboard in grey
        if self.app.hasPasteData():
            all_clipboard_filenames = self.app.getPasteData().getAllFilenames()
        else:
            all_clipboard_filenames = []
        return all_clipboard_filenames

    def getBackgroundColour( self ):
        pi = self.app.frame.tree_panel.getProjectTopProjectInfo()
        if pi.use_background_colour:
            return pi.background_colour
        else:
            return (255,255,255)

    #------------------------------------------------------------
    def Cmd_File_EditCopy( self, all_rows ):
        self.app.setPasteData( wb_clipboard.Clipboard( [self.getFilename( row ) for row in all_rows], is_copy=True ) )
        print T_('Copied %d files to the Clipboard') % len(all_rows)
        self.app.refreshFrame()
 
    def Cmd_File_EditCut( self, all_rows ):
        self.app.setPasteData( wb_clipboard.Clipboard( [self.getFilename( row ) for row in all_rows], is_copy=False ) )
        print T_('Cut %d files to the Clipboard') % len(all_rows)
        self.app.refreshFrame()

    def Cmd_File_EditPaste( self, all_rows ):
        if not self.app.hasPasteData():
            return

        paste_data = self.app.getPasteData()
        self.app.clearPasteData()

        all_status = []
        try:
            for filename in paste_data.getAllFilenames():
                if os.path.isdir( filename ):
                    dir_status = self.project_info.client_bg.status( os.path.dirname( filename ), recurse=False )
                    all_status.extend( [s for s in dir_status if s.path == filename] )
                else:
                    all_status.extend( self.project_info.client_bg.status( filename, recurse=False ) )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
            return

        if paste_data.isCopy():
            title = T_('Paste Copy')
        else:
            title = T_('Paste Move')

        confirmed, force = self.app.confirmForceAction( title, self.getStatusAndFilenames( all_status ) )
        if not confirmed:
            return

        self.app.setProgress( title, 0 )

        for status in all_status:
            ok = False

            old_filename = status.path
            basename = os.path.basename( old_filename )
            new_filename = os.path.join( self.project_info.wc_path, basename )

            if paste_data.isCopy():
                rename_title = T_('Save As')
            else:
                rename_title = T_('Rename')

            while os.path.exists( new_filename ):
                new_name, force = self.app.renameFile( rename_title, os.path.basename( old_filename ), None )
                if new_name is None:
                    return
                new_filename = os.path.join( self.project_info.wc_path, new_name )

            self.app.log.info( T_('%(title)s: From %(filename)s') %
                                {'title': title
                                ,'filename': old_filename} )
            self.app.log.info( T_('%(title)s:   To %(filename)s') %
                                {'title': title
                                ,'filename': new_filename} )

            is_controlled = self.isControlled( status )

            yield self.app.backgroundProcess

            try:
                if paste_data.isCopy():
                    if os.path.isdir( old_filename ):
                        if is_controlled:
                            self.project_info.client_bg.copy( old_filename, new_filename )
                        else:
                            raise EnvironmentError( 'TBD - implement copy of folder' )
                            os.copydirtree( old_filename, new_filename )
                    else:
                        self.__copyFile( old_filename, new_filename, is_controlled, status.text_status, status.prop_status )

                    ok = True
                else:
                    if os.path.isdir( old_filename ):
                        if is_controlled:
                            self.project_info.client_bg.move( old_filename, new_filename, force=force )
                        else:
                            os.rename( old_filename, new_filename )
                    else:
                        text_status = self.getTextStatus( status )
                        prop_status = self.getPropStatus( status )
                        self.__moveFile( old_filename, new_filename, is_controlled, text_status, prop_status )

                    ok = True

            except EnvironmentError, e:
                self.app.log.error( str(e) )

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

        self.app.clearProgress()
        self.app.refreshFrame()


    #------------------------------------------------------------
    def Cmd_File_Add( self, all_rows ):
        try:
            for filename in [self.getFilename( row ) for row in all_rows]:
                self.project_info.client_fg.add( filename )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.app.refreshFrame()

    # Cmd_File_Annotate - from SubversionListHandlerCommon

    def Cmd_File_Checkin( self, all_rows ):
        if len(all_rows) == 0:
            wx.MessageBox( T_("There are no changes to check in"),
                T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            return

        all_files = [self.all_files[ row ] for row in all_rows]


        ci_frame = wb_subversion_checkin.CheckinFrame( self.app, self.project_info, all_files )
        ci_frame.Show( True )

    def Cmd_File_Cleanup( self, all_rows ):
        try:
            for filename in [self.getFilename( row ) for row in all_rows]:
                self.project_info.client_fg.cleanup( filename )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
        self.app.refreshFrame()

    def Cmd_File_Delete( self, all_rows ):
        if not self.app.confirmAction( T_('Delete File'), self.getStatusAndFilenames( all_rows ) ):
            return

        for filename, is_controlled, text_status, prop_status in [
                (self.getFilename( row ), self.isControlled( row ), self.getTextStatus( row ), self.getPropStatus( row ))
                    for row in all_rows]:
            try:
                if is_controlled:
                    if text_status == pysvn.wc_status_kind.added:
                        self.project_info.client_fg.revert( filename )
                        os.remove( filename )

                    elif( text_status == pysvn.wc_status_kind.modified
                    or prop_status == pysvn.wc_status_kind.modified ):
                        self.project_info.client_fg.revert( filename )
                        self.project_info.client_fg.remove( filename )

                    else:
                        self.project_info.client_fg.remove( filename )

                else:
                    os.remove( filename )

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            except EnvironmentError, e:
                self.app.log.error( str(e) )

        self.app.refreshFrame()

    # Cmd_File_DiffWorkBase - from SubversionListHandlerCommon
    # Cmd_File_DiffWorkHead - from SubversionListHandlerCommon

    def Cmd_File_DiffOldNew( self, all_rows ):
        for row in all_rows:
            old_filename = self.getConflictOld( row )
            new_filename = self.getConflictNew( row )
            # qqq diff old_filename@None, new_filename@None
            self.app.diffFiles( old_filename, old_filename, new_filename, new_filename )

    def Cmd_File_DiffOldMine( self, all_rows ):
        for row in all_rows:
            old_filename = self.getConflictOld( row )
            mine_filename = self.getConflictMine( row )
            # qqq diff old_filename@None, mine_filename@None
            self.app.diffFiles( old_filename, old_filename, mine_filename, mine_filename )

    def Cmd_File_DiffMineNew( self, all_rows ):
        for row in all_rows:
            mine_filename = self.getConflictMine( row )
            new_filename = self.getConflictNew( row )
            # qqq diff mine_filename@None, new_filename@None
            self.app.diffFiles( mine_filename, mine_filename, new_filename, new_filename )

    # Cmd_File_History = from SubversionListHandlerCommon
    # Cmd_File_Info = from SubversionListHandlerCommon
    # Cmd_File_Lock= from SubversionListHandlerCommon
    # Cmd_File_Properties - from SubversionListHandlerCommon
    def __copyFile( self, old_filename, new_full_filename, is_controlled, text_status, prop_status ):
        if not is_controlled:
            raise EnvironmentError( 'TBD - copy file' )
            os.rename( old_filename, new_full_filename )
            return

        if( text_status == pysvn.wc_status_kind.normal
        and prop_status in [pysvn.wc_status_kind.normal, pysvn.wc_status_kind.none] ):
            self.project_info.client_fg.copy( old_filename, new_full_filename )
        else:
            raise EnvironmentError( 'Cannot copy an added or modified file' )

    def __moveFile( self, old_filename, new_full_filename, is_controlled, text_status, prop_status ):
        if not is_controlled:
            os.rename( old_filename, new_full_filename )
            return

        if text_status == pysvn.wc_status_kind.added:
            # need to save and restore the props around the rename dance
            all_prop_lists = self.project_info.client_fg.proplist( old_filename,
                            revision=pysvn.Revision( pysvn.opt_revision_kind.working ) )
            self.project_info.client_fg.revert( old_filename )
            print( T_('Rename %(from)s %(to)s') %
                    {'from': old_filename
                    ,'to': new_full_filename} )
            os.rename( old_filename, new_full_filename )
            self.project_info.client_fg.add( new_full_filename )

            # all_prop_lists is empty if there are no properties set
            if len(all_prop_lists) > 0:
                _, prop_dict = all_prop_lists[0]

                for prop_name, prop_value in prop_dict.items():
                    self.project_info.client_fg.propset( prop_name, prop_value, new_full_filename )

        elif( text_status == pysvn.wc_status_kind.modified
        or prop_status == pysvn.wc_status_kind.modified ):
            new_full_tmp_filename = None
            for tmp_name_index in range( 100 ):
                tmp_filename = os.path.join( os.path.dirname( old_filename ),
                    '%s.%d.tmp' % (new_full_filename, tmp_name_index) )
                if not os.path.exists( tmp_filename ):
                    new_full_tmp_filename = tmp_filename
                    break

            if new_full_tmp_filename is None:
                self.app.log.error( T_('Failed to create tmp file for rename') )
            else:
                # need to save and restore the props around the rename dance
                all_props = self.project_info.client_fg.proplist( old_filename,
                                revision=pysvn.Revision( pysvn.opt_revision_kind.working ) )

                print( T_('Rename %(from)s %(to)s') %
                        {'from': old_filename
                        ,'to': new_full_tmp_filename} )
                os.rename( old_filename, new_full_tmp_filename )
                self.project_info.client_fg.revert( old_filename )
                self.project_info.client_fg.move( old_filename, new_full_filename )
                os.remove( new_full_filename )

                print( T_('Rename %(from)s %(to)s') %
                            {'from': new_full_tmp_filename
                            ,'to': new_full_tmp_filename} )
                os.rename( new_full_tmp_filename, new_full_filename )

                if len(all_props) > 0:
                    _, prop_dict = all_props[0]
                    for prop_name, prop_value in prop_dict.items():
                        self.project_info.client_fg.propset( prop_name, prop_value, new_full_filename )
        else:
            self.project_info.client_fg.move( old_filename, new_full_filename )

    def Cmd_File_Rename( self, all_rows ):
        for old_filename, is_controlled, text_status, prop_status in [
                (self.getFilename( row ), self.isControlled( row ), self.getTextStatus( row ), self.getPropStatus( row ))
                    for row in all_rows]:
            old_name = os.path.basename( old_filename )

            new_name, force = self.app.renameFile( T_("Rename"), old_name, None )

            if new_name is None:
                break

            if new_name != old_name:
                new_full_filename = os.path.join( os.path.dirname( old_filename ), new_name )
                print T_('Rename'),old_filename, new_full_filename
                try:
                    self.__moveFile( old_filename, new_full_filename, is_controlled, text_status, prop_status )
                except pysvn.ClientError, e:
                    self.app.log_client_error( e )
                    break
                except EnvironmentError, e:
                    self.app.log.error( str(e) )
                    break

        self.app.refreshFrame()

    def Cmd_File_Revert( self, all_rows ):
        if not self.app.confirmAction( T_('Revert'), self.getStatusAndFilenames( all_rows ) ):
            return

        try:
            for filename in [self.getFilename( row ) for row in all_rows]:
                self.project_info.client_fg.revert( filename )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
        self.app.refreshFrame()

    def Cmd_File_Resolved( self, all_rows ):
        if not self.app.confirmAction( T_('Resolved'), self.getStatusAndFilenames( all_rows ) ):
            return

        try:
            for filename in [self.getFilename( row ) for row in all_rows]:
                self.project_info.client_fg.resolved( filename )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
        self.app.refreshFrame()

    # Cmd_File_Unlock= from SubversionListHandlerCommon
    def Cmd_File_Update( self, all_rows ):
        rev = pysvn.Revision( pysvn.opt_revision_kind.head )

        self.app.setProgress( T_('Updated %(count)d'), 0 )

        self.project_info.initNotify()

        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setAction( T_('Update %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                rev_list = self.project_info.client_bg.update( filename, recurse=False, revision=rev )
                ok = True

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

            for rev in rev_list:
                if rev.number > 0:
                    basename = os.path.basename( filename )
                    count = self.app.getProgressValue( 'count' )
                    if count == 0:
                        self.app.log.info( T_('Updated %(filename)s to revision %(rev)d, no new updates') %
                                                {'filename': basename
                                                ,'rev': rev.number} )
                    else:
                        self.app.log.info( S_('Updated %(filename)s to revision %(rev)d, %(count)d new update', 
                                              'Updated %(filename)s to revision %(rev)d, %(count)d new updates', count) %
                                                {'filename': basename
                                                ,'rev': rev.number
                                                ,'count': count} )

        if self.project_info.notification_of_files_in_conflict > 0:
            wx.MessageBox( S_("%d file is in conflict", 
                              "%d files are in conflict", self.project_info.notification_of_files_in_conflict) % self.project_info.notification_of_files_in_conflict,
                T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_File_UpdateTo( self, all_rows ):
        dialog = wb_dialogs.UpdateTo( None, T_('Update to revision') )
        if dialog.ShowModal() != wx.ID_OK:
            return

        rev = dialog.getRevision()

        self.app.setProgress( T_('Updated %(count)d'), 0 )

        self.project_info.initNotify()

        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setAction( T_('Update %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                rev_list = self.project_info.client_bg.update( filename, recurse=False, revision=rev )
                ok = True

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

            for rev in rev_list:
                if rev.number > 0:
                    basename = os.path.basename( filename )
                    count = self.app.getProgressValue( 'count' )
                    if count == 0:
                        self.app.log.info( T_('Updated %(filename)s to revision %(rev)d, no new updates') % 
                                                {'filename': basename
                                                ,'rev': rev.number} )
                    else:
                        self.app.log.info( S_('Updated %(filename)s to revision %(rev)d, %(count)d new update', 
                                              'Updated %(filename)s to revision %(rev)d, %(count)d new updates', count) %
                                                {'filename': basename
                                                ,'rev': rev.number
                                                ,'count': count} )

        if self.project_info.notification_of_files_in_conflict > 0:
            wx.MessageBox( S_("%d file is in conflict", 
                              "%d files are in conflict", self.project_info.notification_of_files_in_conflict) % self.project_info.notification_of_files_in_conflict,
                              T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_File_Switch ( self ):
        dialog = wb_dialogs.Switch( self.app.frame.tree_panel.tree_ctrl, self.app, self.project_info.wc_path, T_('Switch to Branch/Tag') )
        if dialog.ShowModal() != wx.ID_OK:
            return

        to_url, recurse, svndepth = dialog.getValues()

        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setAction( T_('Switch %s...') % filename )

            yield self.app.backgroundProcess

            try:
                if recurse:
                    self.project_info.client_fg.switch( filename, to_url, depth=svndepth,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                else:
                    self.project_info.client_fg.switch( filename, to_url, recurse=True,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

