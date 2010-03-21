'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_tree_handler.py

'''
import os
import types

import pysvn

import wx

import wb_tree_panel
import wb_ids
import wb_subversion_utils
import wb_subversion_project_info
import wb_subversion_utils
import wb_subversion_diff
import wb_subversion_info_dialog
import wb_subversion_history
import wb_subversion_checkin
import wb_subversion_report_updates
import wb_subversion_report_lock
import wb_subversion_report_branch_changes
import wb_subversion_properties_dialog
import wb_clipboard
import wb_dialogs
import wb_config

class SubversionProject(wb_tree_panel.TreeProjectItem):
    def __init__( self, app, project_info ):
        wb_tree_panel.TreeProjectItem.__init__( self )
        self.project_info = project_info
        self.app = app

        self.__log_message = None

    def updateStatus( self ):
        self.project_info.updateStatus()

    def getProjectInfo( self ):
        return self.project_info

    def mayExpand( self ):
        dir_status = self.project_info.getDirStatus()
        if dir_status is None:
            # no status available - make a guess
            if not os.path.exists( self.project_info.wc_path ):
                # nothing there 
                return False
            else:
                # some dir assume can expand
                return True

        for file in self.project_info.getTreeFilesStatus():
            if( (file.entry is not None and file.entry.kind == pysvn.node_kind.dir)
            or (file.entry is None and os.path.isdir( file.path )) ):
                return True

        return False

    def getExpansion( self ):
        project_info_list = []

        for file in self.project_info.getTreeFilesStatus():

            if( (file.entry is None and os.path.isdir( file.path ))
            or (file.entry is not None and file.entry.kind == pysvn.node_kind.dir) ):
                pi = wb_subversion_project_info.ProjectInfo( self.app, self.project_info )
                name = os.path.basename( file.path )
                if file.entry is None or file.entry.url is None:
                    # fake up the url - maybe a failed checkout/update
                    url = '%s/%s' % (self.project_info.url, name )
                else:
                    url = file.entry.url

                pi.init( name, url=url, wc_path=file.path,
                    client_fg=self.project_info.client_fg,
                    client_bg=self.project_info.client_bg )
                project_info_list.append( pi )

        return project_info_list

    def getTreeNodeColour( self ):
        dir_status = self.project_info.getDirStatus()
        if dir_status is None:
            # no status available - make a guess
            if not os.path.exists( self.project_info.wc_path ):
                # nothing there
                return wb_config.colour_status_need_checkout
            elif not os.path.exists( os.path.join( self.project_info.wc_path, '.svn' ) ):
                # not versioned
                return wb_config.colour_status_unversioned
            else:
                # versioned and present
                return wb_config.colour_status_normal

        elif not os.path.exists( dir_status.path ):
            # nothing there
            return wb_config.colour_status_need_checkout
        elif dir_status.text_status in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
            # unversioned
            return wb_config.colour_status_unversioned

        # versioned and present
        return wb_config.colour_status_normal
    
    def getState( self ):
        state = wb_tree_panel.TreeState()

        dir_status = self.project_info.getDirStatus()

        state.is_project_parent = self.is_project_parent

        if dir_status is None:
            state.modified = False
            state.new_versioned = False
            state.versioned = True
            state.unversioned = False
            state.need_checkin = False
            state.need_checkout = True
            state.conflict = False
            state.file_exists = False
            state.revertable = False

        else:
            state.modified = True
            state.new_versioned = True
            state.versioned = True
            state.unversioned = True
            state.need_checkin = True
            state.need_checkout = False
            state.conflict = True
            state.file_exists = True

            if not os.path.exists( dir_status.path ):
                state.file_exists = False

            text_status = dir_status.text_status
            if text_status in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
                state.versioned = False
            else:
                state.unversioned = False

            state.new_versioned = state.new_versioned and text_status in [pysvn.wc_status_kind.added]

            prop_status = dir_status.prop_status
            state.modified = (text_status in [pysvn.wc_status_kind.modified,
                                                pysvn.wc_status_kind.conflicted]
                            or
                                prop_status in [pysvn.wc_status_kind.modified,
                                                pysvn.wc_status_kind.conflicted])
            state.need_checkin = (text_status in [pysvn.wc_status_kind.added,
                                                    pysvn.wc_status_kind.deleted,
                                                    pysvn.wc_status_kind.modified]
                                or
                                    prop_status in [pysvn.wc_status_kind.added,
                                                    pysvn.wc_status_kind.deleted,
                                                    pysvn.wc_status_kind.modified])
            state.conflict = text_status in [pysvn.wc_status_kind.conflicted]

            state.revertable = state.conflict or state.modified or state.need_checkin or not state.file_exists

        return state

    def getContextMenu( self, state ):
        menu_item =[('', wb_ids.id_Command_Shell, T_('&Command Shell') )
            ,('', wb_ids.id_File_Browser, T_('&File Browser') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_DiffWorkBase, T_('Diff WC vs. BASE...') )
            ,('', wb_ids.id_SP_DiffWorkHead, T_('Diff WC vs. HEAD...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_History, T_('Log history...') )
            ,('', wb_ids.id_SP_Info, T_('Information...') )
            ,('', wb_ids.id_SP_Properties, T_('Properties...') )
            ,('-', 0, 0 )]
        if not state.file_exists and state.versioned and self.isProjectParent():
            menu_item += [('', wb_ids.id_SP_Checkout, T_('Checkout') )]
            menu_item += [('', wb_ids.id_SP_CheckoutTo, T_('Checkout to...') )]
        else:
            menu_item += [('', wb_ids.id_SP_Update, T_('Update') )]
            menu_item += [('', wb_ids.id_SP_UpdateTo, T_('Update to..') )]
        menu_item += [('-', 0, '' )
            ,('', wb_ids.id_SP_Checkin, T_('Checkin...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_NewFile, T_('New File...') )
            ,('', wb_ids.id_SP_Mkdir, T_('Make directory...') )
            ,('', wb_ids.id_SP_Add, T_('Add...') )
            ,('', wb_ids.id_SP_Rename, T_('Rename...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Delete, T_('Delete...') )
            ,('', wb_ids.id_SP_Revert, T_('Revert...') )
            ,('-', 0, 0 )
            ,('', wb_ids.id_SP_Cleanup, T_('Clean up') )
            ]

        return wb_subversion_utils.populateMenu( wx.Menu(), menu_item )

    def Cmd_Dir_CreateBranch( self ):
        # must return the generator
        return self.__copyToHelper( self.project_info.getBranchesUrl, wb_dialogs.CreateBranch, T_('Creating branch %s') )

    def Cmd_Dir_CreateTag( self ):
        # must return the generator
        return self.__copyToHelper( self.project_info.getTagsUrl, wb_dialogs.CreateTag, T_('Creating tag %s') )

    def __getLogMessage( self ):
        return True, self.__log_message

    # generator function - needs to be pumped
    def __copyToHelper( self, get_url_fn, dialog_class, status_title ):
        info = self.project_info.client_bg.info2( self.project_info.wc_path, recurse=False )[0][1]
        copy_from_url = info.URL
        copy_to_root_url = get_url_fn( copy_from_url )

        dialog = dialog_class( self.app.frame.tree_panel.tree_ctrl, self.app, copy_from_url, copy_to_root_url )
        if dialog.ShowModal() != wx.ID_OK:
            return

        copy_to_leaf_url = dialog.getCopyToLeaf()
        copy_to_url = dialog.getCopyTo()
        self.__log_message = dialog.getLogMessage().encode( 'utf-8' )

        print status_title % copy_to_url
        self.app.setAction( status_title % copy_to_leaf_url )

        yield self.app.backgroundProcess
        self.project_info.client_bg.callback_get_log_message = self.__getLogMessage
        try:
            self.project_info.client_bg.copy( copy_from_url,copy_to_url )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.project_info.client_bg.callback_get_log_message = None
        yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Dir_EditCopy( self ):
        self.app.setPasteData( wb_clipboard.Clipboard( [self.project_info.wc_path], is_copy=True ) )
        print T_('Copied folder %s to the Clipboard') % self.project_info.wc_path
        self.app.refreshFrame()
 
    def Cmd_Dir_EditCut( self ):
        self.app.setPasteData( wb_clipboard.Clipboard( [self.project_info.wc_path], is_copy=False ) )
        print T_('Cut folder %s to the Clipboard') % self.project_info.wc_path
        self.app.refreshFrame()

    def Cmd_Dir_EditPaste( self ):
        return self.app.frame.list_panel.OnSpEditPaste()

    def Cmd_Dir_Add( self ):
        name = os.path.basename( self.project_info.wc_path )
        force, recursive = self.app.addFolder( T_('Add Folder'), name, force=False, recursive=True )
        if force is None:
            return

        try:
            self.project_info.client_fg.add( self.project_info.wc_path, force=force, recurse=recursive )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.app.refreshFrame()

    def Cmd_Dir_Checkout( self ):
        self.app.setAction( T_('Checkout %s...') % self.project_info.url )

        yield self.app.backgroundProcess
        self.__checkoutToRevision( pysvn.Revision( pysvn.opt_revision_kind.head ), True, None )

        yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Dir_CheckoutTo( self ):
        dialog = wb_dialogs.UpdateTo( None, T_('Checkout to revision') )
        if dialog.ShowModal() == wx.ID_OK:
            recursive, svndepth = dialog.getSvnDepth()
            self.app.setAction( T_('Checkout %s...') % self.project_info.url )

            yield self.app.backgroundProcess
            self.__checkoutToRevision( dialog.getRevision(), recursive, svndepth )

            yield self.app.foregroundProcess

            self.app.setAction( T_('Ready') )
            self.app.refreshFrame()

    def __checkoutToRevision( self, rev, recursive, svndepth ):
        try:
            # lose any trailing / on the URL it stops checkout working
            url = self.project_info.url
            if url[-1] == '/':
                url = url[:-1]
            if recursive:
                self.project_info.client_bg.checkout( url, self.project_info.wc_path, recurse=True, revision=rev )

            else:
                self.project_info.client_bg.checkout( url, self.project_info.wc_path, depth=svndepth, revision=rev )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

    def Cmd_Dir_Cleanup( self ):
        self.app.setAction( T_('Clean up %s...') % self.project_info.wc_path )

        yield self.app.backgroundProcess
        try:
            self.project_info.client_bg.cleanup( self.project_info.wc_path )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Dir_Checkin( self ):
        # get a status output to show the user

        self.app.setAction( T_('Look for changes to check in %s...') % self.project_info.wc_path )

        error = False
        yield self.app.backgroundProcess
        try:
            all_files = self.project_info.client_bg.status(
                self.project_info.wc_path,
                recurse=True, get_all=False,
                ignore=True, update=False )
            all_files = [entry for entry in all_files
                            if wb_subversion_utils.wc_status_checkin_map[ entry.text_status ]
                            or wb_subversion_utils.wc_status_checkin_map[ entry.prop_status ]]
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
            error = True
        yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )

        if error:
            return

        if len(all_files) == 0:
            wx.MessageBox( T_("There are no changes to check in"),
                T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            return

        ci_frame = wb_subversion_checkin.CheckinFrame( self.app, self.project_info, all_files )
        ci_frame.Show( True )

    def __cmd_status_output( self, all_files ):
        output_lines = []
        all_files.sort( wb_subversion_utils.by_path )
        for file in all_files:
            state = wb_subversion_utils._status_format( file )

            if( wb_subversion_utils.wc_status_checkin_map[ file.text_status ]
            or  wb_subversion_utils.wc_status_checkin_map[ file.prop_status ] ):
                output_lines.append( (state, file.path) )

        return output_lines

    def Cmd_Dir_Delete( self ):
        confirmed, force = self.app.confirmForceAction( T_('Delete Folder'), [('', self.project_info.wc_path)] )
        if confirmed:
            try:
                self.project_info.client_fg.remove( self.project_info.wc_path, force=force )
            except pysvn.ClientError, e:
                self.app.log_client_error( e )
            self.app.refreshFrame()

    def Cmd_Dir_DiffWorkBase( self ):
        filename = self.project_info.wc_path

        self.app.setAction( T_('Diff BASE %s...') % filename )

        info1 = wb_subversion_diff.PathInfoForDiff()

        info1.path = filename
        info1.revision = pysvn.Revision( pysvn.opt_revision_kind.base )
        info1.title = filename + '@BASE'

        info2 = wb_subversion_diff.PathInfoForDiff()

        info2.path = filename
        info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
        info2.title = filename

        generator = wb_subversion_diff.subversionDiffDir(
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

    def Cmd_Dir_DiffWorkHead( self ):
        filename = self.project_info.wc_path

        self.app.setAction( T_('Diff HEAD %s...') % filename )


        info1 = wb_subversion_diff.PathInfoForDiff()

        info1.path = filename
        info1.revision = pysvn.Revision( pysvn.opt_revision_kind.head )
        info1.title = filename + '@HEAD'

        info2 = wb_subversion_diff.PathInfoForDiff()

        info2.path = filename
        info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
        info2.title = filename

        generator = wb_subversion_diff.subversionDiffDir(
                            self.app,
                            self.project_info,
                            info1,  info2 )

        if type(generator) == types.GeneratorType:
            while True:
                try:
                    where_to_go_next = generator.next()
                except StopIteration:
                    # no problem all done
                    break

                yield where_to_go_next

        self.app.setAction( T_('Ready') )


    def Cmd_Dir_History( self ):
        filename = self.project_info.wc_path

        dialog = wb_subversion_history.LogHistoryDialog( self.app, self.app.frame.tree_panel.tree_ctrl )
        result = dialog.ShowModal()
        if result != wx.ID_OK:
            return

        self.app.setAction( T_('Log history %s...') % filename )

        yield self.app.backgroundProcess

        ok = False
        history_entries = []
        try:
            file_url, history_entries = wb_subversion_history.getHistoryEntries(
                        self.project_info,
                        filename,
                        dialog.getLimit(),
                        dialog.getRevisionEnd(),
                        dialog.getIncludeTags() )
            ok = True
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        if ok:
            h_frame = wb_subversion_history.HistoryDirFrame(
                self.app,
                self.project_info,
                filename,
                file_url,
                history_entries )
            h_frame.Show( True )

        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Dir_Info( self ):
        filename = self.project_info.wc_path

        try:
            if hasattr( self.project_info.client_fg, 'info2' ):
                entry = self.project_info.client_fg.info2( filename, recurse=False )
            else:
                entry = self.project_info.client_fg.info( filename )

            dialog = wb_subversion_info_dialog.InfoDialog( self.app,
                    self.app.frame.tree_panel.tree_ctrl,
                    self.project_info.wc_path,
                    entry )
            dialog.ShowModal()

        except pysvn.ClientError, e:
            self.app.log_client_error( e )


    def Cmd_Dir_Mkdir( self ):
        rc, name = self.app.getFilename( T_('Make directory'), T_('Name:') )
        if not rc:
            return

        try:
            new_path = os.path.join( self.project_info.wc_path, name )
            # pass an empty message
            self.project_info.client_fg.mkdir( new_path,  '' )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        # open up the current tree node to show the created item
        self.app.expandSelectedTreeNode()

    def Cmd_Dir_NewFile( self ):
        pi = self.app.frame.tree_panel.getProjectTopProjectInfo()

        template_dir = ''
        if pi is not None:
            template_dir = pi.new_file_template_dir

        dialog = wb_dialogs.NewFile( self.app.frame.tree_panel.tree_ctrl, template_dir )
        if dialog.ShowModal() == wx.ID_OK:
            template_contents = ''
            if( template_dir != ''
            and dialog.getTemplateFilename() is not None ):
                try:
                    template_filename = os.path.join( template_dir, dialog.getTemplateFilename() )
                    t = file( template_filename, 'r' )
                    template_contents = t.read()
                    t.close()

                except EnvironmentError, e:
                    self.app.log.error( T_('Cannot read template %(filename)s - %(error)s') %
                                    {'filename': new_filename
                                    , 'error': str(e)} )
                    return

            try:
                new_filename = os.path.join( self.project_info.wc_path, dialog.getNewFilename() )
                f = file( new_filename, 'w' )
                f.write( template_contents )
                f.close()

            except EnvironmentError, e:
                self.app.log.error( T_('Cannot create new file %(filename)s - %(error)s') %
                                    {'filename': new_filename
                                    , 'error': str(e)} )
                return

            try:
                self.project_info.client_fg.add( new_filename )
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

        self.app.refreshFrame()

    def Cmd_Dir_Properties( self ):
        client_fg = self.project_info.client_fg

        filename = self.project_info.wc_path

        try:
            prop_list = client_fg.proplist( filename,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.working ) )
            if len(prop_list) == 0:
                prop_dict = {}
            else:
                _, prop_dict = prop_list[0]
            dialog = wb_subversion_properties_dialog.DirPropertiesDialog( self.app,
                    self.app.frame.tree_panel.tree_ctrl,
                    filename,
                    prop_dict )
            if dialog.ShowModal() == wx.OK:
                for present, name, value in dialog.getModifiedProperties():
                    if not present:
                        # delete name
                        client_fg.propdel( name, filename )
                    else:
                        # add/update name value
                        client_fg.propset( name, value, filename )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.app.refreshFrame()

    def Cmd_Dir_ReportLocksWc( self ):
        return self.__reportLocksCommon( show_repos_locks=False )

    def Cmd_Dir_ReportLocksRepos( self ):
        return self.__reportLocksCommon( show_repos_locks=True )

    def __reportLocksCommon( self, show_repos_locks ):

        if show_repos_locks:
            self.app.setAction( T_('Looking for repository locks in %s...') % self.project_info.wc_path )
        else:
            self.app.setAction( T_('Looking for working copy locks in %s...') % self.project_info.wc_path )

        ok = True
        yield self.app.backgroundProcess
        try:
            all_files = self.project_info.client_bg.status(
                self.project_info.wc_path,
                recurse=True, get_all=False,
                ignore=True, update=show_repos_locks )
            all_files = [status for status in all_files
                            if (status.entry is not None and status.entry.lock_token is not None)
                            or (status.repos_lock is not None)]
        except pysvn.ClientError, e:
            self.app.log_client_error( e )
            ok = False
        yield self.app.foregroundProcess

        self.app.setAction( T_('Ready') )

        if not ok:
            return

        if len(all_files) == 0:
            if show_repos_locks:
                wx.MessageBox( T_("There are no locked files in the repository"),
                    T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            else:
                wx.MessageBox( T_("There are no locked files in the working copy"),
                    T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            return

        ci_frame = wb_subversion_report_lock.ReportLockFrame(
                        self.app, self.project_info, all_files,
                        show_repos_locks=show_repos_locks )
        ci_frame.Show( True )

    def Cmd_Dir_ReportUpdates( self ):
        self.app.setAction( T_('Updates %s...') % self.project_info.url )

        ok = False
        all_files = []

        yield self.app.backgroundProcess
        try:
            all_files = self.project_info.client_bg.status(
                self.project_info.wc_path,
                recurse=True, get_all=False,
                ignore=True, update=True )
            ok = True

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        if len(all_files) == 0:
            wx.MessageBox( T_("All files are up todate"),
                T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            return

        self.app.setAction( T_('Ready') )

        if ok:
            all_files = [status for status in all_files
                            if status.repos_prop_status != pysvn.wc_status_kind.none
                            or (status.entry is not None
                                and status.entry.kind == pysvn.node_kind.file
                                and status.repos_text_status != pysvn.wc_status_kind.none)]
            ci_frame = wb_subversion_report_updates.ReportUpdatesFrame( self.app, self.project_info, all_files )
            ci_frame.Show( True )

    def Cmd_Dir_ReportBranchChanges( self ):
        self.app.setAction( T_('Branch changes %s...') % self.project_info.url )

        changed_files = []
        is_branch = False

        yield self.app.backgroundProcess

        try:
            log_entries = self.project_info.client_bg.log( self.project_info.url, discover_changed_paths=True )
            if log_entries[-1]['changed_paths'][0]['copyfrom_path'] is not None:
                is_branch = True
                changed_states = {}
                prefix_len = len( log_entries[-1]['changed_paths'][0]['path'] )
                repos_root_url = self.project_info.client_bg.info2( self.project_info.wc_path )[0][1]['repos_root_URL']
                local_states = self.project_info.client_bg.status( self.project_info.wc_path, recurse=True,
                                                                   get_all=True, ignore=True, update=False )
                for log_entry in reversed(log_entries[:-1]):
                    for changed_path in log_entry['changed_paths']:
                        repository_path = changed_path['path']
                        url = repos_root_url + repository_path

                        local_path = self.project_info.wc_path + repository_path[prefix_len:].replace( '/', os.path.sep )
                        if changed_states.has_key(local_path):
                            branch_text_states = changed_states[local_path]['branch_text_states']
                        else:
                            branch_text_states = ''
                        branch_text_states += changed_path['action'].lower()

                        # Create a new status object from the log entry data.
                        entry = pysvn.PysvnEntry(
                                    {'checksum': ''
                                    ,'commit_author': log_entry.author
                                    ,'commit_revision': log_entry.revision
                                    ,'commit_time': log_entry.date
                                    ,'conflict_new': None
                                    ,'conflict_old': None
                                    ,'conflict_work': None
                                    ,'copy_from_revision': pysvn.Revision( pysvn.opt_revision_kind.number, -1 )
                                    ,'copy_from_url': None
                                    ,'is_absent': 0
                                    ,'is_copied': 0
                                    ,'is_deleted': 0
                                    ,'kind': pysvn.node_kind.file
                                    ,'lock_comment': None
                                    ,'lock_creation_date': 0.0
                                    ,'lock_owner': None
                                    ,'lock_token': None
                                    ,'name': repository_path.split( '/' )[-1]
                                    ,'properties_time': 0.0
                                    ,'property_reject_file': None
                                    ,'repos': repos_root_url
                                    ,'revision': log_entry.revision
                                    ,'schedule': pysvn.wc_schedule.normal
                                    ,'text_time': 0.0
                                    ,'url': url
                                    ,'uuid': ''})
                        status = pysvn.PysvnStatus(
                                    {'entry': entry
                                    ,'is_copied': 0
                                    ,'is_locked': 0
                                    ,'is_switched': 0
                                    ,'is_versioned': 1
                                    ,'path': local_path
                                    ,'prop_status': pysvn.wc_status_kind.normal
                                    ,'repos_lock': None
                                    ,'repos_prop_status': pysvn.wc_status_kind.none
                                    ,'repos_text_status': pysvn.wc_status_kind.none
                                    ,'branch_text_states': branch_text_states
                                    ,'text_status': pysvn.wc_status_kind.normal})
                        changed_states[local_path] = status

                for status in local_states:
                    if( status.entry is not None
                    and ((status.text_status not in (pysvn.wc_status_kind.normal, pysvn.wc_status_kind.none))
                        or
                        (status.prop_status not in (pysvn.wc_status_kind.normal, pysvn.wc_status_kind.none))) ):
                        if changed_states.has_key( status.path ):
                            status['branch_text_states'] = changed_states[status.path]['branch_text_states']
                        changed_states[status.path] = status

                changed_files = [changed_states[status] for status in changed_states]

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        if not is_branch:
            wx.MessageBox( T_('"%s" is not a branch.') % self.project_info.url, T_("Error"), style=wx.OK|wx.ICON_ERROR )
        elif len( changed_files ) == 0:
            wx.MessageBox( T_('No files changed yet in branch "%s".') % self.project_info.url, T_("Error"), style=wx.OK|wx.ICON_ERROR )
        else:
            ci_frame = wb_subversion_report_branch_changes.ReportBranchChangesFrame( self.app, self.project_info, changed_files )
            ci_frame.Show( True )

        self.app.setAction( T_('Ready') )


    def Cmd_Dir_Rename( self ):
        old_filename = self.project_info.wc_path
        old_name = os.path.basename( old_filename )

        new_name, force = self.app.renameFile( T_("Rename Directory"), old_name, False )

        if new_name is None:
            return

        if new_name != old_name:
            new_full_filename = os.path.join( os.path.dirname( old_filename ), new_name )
            dir_status = self.project_info.getDirStatus()
            print T_('Rename'), old_filename, new_full_filename
            if dir_status is None or dir_status.text_status not in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
                try:
                    self.project_info.client_fg.move( old_filename, new_full_filename, force=force )
                except pysvn.ClientError, e:
                    self.app.log_client_error( e )
            else:
                try:
                    os.rename( old_filename, new_full_filename )
                except (OSError,IOError), e:
                    self.app.log.error( str(e) )

            self.app.selectTreeNodeInParent( new_name )
        self.app.refreshFrame()

    def Cmd_Dir_Revert( self ):
        # get a status output to show the user
        all_files = self.project_info.client_fg.status( self.project_info.wc_path, recurse=True, get_all=False, ignore=True, update=False )
        status_output = self.__cmd_status_output( all_files )
        if len(status_output) == 0:
            wx.MessageBox( T_("There are no changes to revert"),
                T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )
            return


        if self.app.confirmAction( T_('Revert'), status_output ):
            try:
                self.project_info.client_fg.revert( self.project_info.wc_path, recurse=True )
            except pysvn.ClientError, e:
                self.app.log_client_error( e )
            self.app.refreshFrame()

    def Cmd_Dir_Update( self ):
        self.app.setAction( T_('Update %s...') % self.project_info.wc_path )
        self.app.setProgress( T_('Updated %(count)d'), 0 )

        yield self.app.backgroundProcess
        rev_list = self.__updateToRevision( pysvn.Revision( pysvn.opt_revision_kind.head ), True, None )

        yield self.app.foregroundProcess
        self.__updateToRevisionProcessResults( rev_list )

    def Cmd_Dir_UpdateTo( self ):
        dialog = wb_dialogs.UpdateTo( None, T_('Update to revision') )
        if dialog.ShowModal() != wx.ID_OK:
            return

        recursive, svndepth = dialog.getSvnDepth()

        self.app.setAction( T_('Update %s...') % self.project_info.wc_path )
        self.app.setProgress( T_('Updated %(count)d'), 0 )

        yield self.app.backgroundProcess
        rev_list = self.__updateToRevision( dialog.getRevision(), recursive, svndepth )

        yield self.app.foregroundProcess
        self.__updateToRevisionProcessResults( rev_list )

    def __updateToRevision( self, rev, recursive, svndepth ):
        filename = self.project_info.wc_path
        try:
            self.project_info.initNotify()

            if recursive:
                rev_list = self.project_info.client_bg.update( filename, recurse=True, revision=rev )
            else:
                rev_list = self.project_info.client_bg.update( filename, depth=svndepth, revision=rev )

            return rev_list

        except pysvn.ClientError, e:
            self.app.log_client_error( e )

            return None
        
    def __updateToRevisionProcessResults( self, rev_list ):
        filename = self.project_info.wc_path
        if rev_list is not None:
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
                else:
                    self.app.log.warning( T_('Already up to date') )

            if self.project_info.notification_of_files_in_conflict > 0:
                wx.MessageBox( S_("%d file is in conflict", 
                                  "%d files are in conflict", self.project_info.notification_of_files_in_conflict) % self.project_info.notification_of_files_in_conflict,
                               T_("Warning"), style=wx.OK|wx.ICON_EXCLAMATION )

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Dir_Copy( self, all_filenames ):
        try:
            for src_filename in all_filenames:
                self.project_info.client_fg.copy( src_filename, self.project_info.wc_path )
                self.app.log.info( T_('Copied %(from)s to %(to)s') %
                                        {'from': src_filename
                                        ,'to': self.project_info.wc_path} )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.app.refreshFrame()

    def Cmd_Dir_Move( self, all_filenames ):
        try:
            for src_filename in all_filenames:
                self.project_info.client_fg.move( src_filename, self.project_info.wc_path )
                self.app.log.info( T_('Moved %(from)s to %(to)s') %
                                        {'from': src_filename
                                        ,'to': self.project_info.wc_path} )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        self.app.refreshFrame()
