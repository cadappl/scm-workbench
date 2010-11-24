'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_list_handler_common.py

'''
import os
import types

import pysvn
import wx

import wb_subversion_history
import wb_subversion_annotate
import wb_list_panel_common
import wb_exceptions
import wb_subversion_utils
import wb_read_file
import wb_subversion_info_dialog
import wb_subversion_properties_dialog
import wb_subversion_diff
import wb_config

col_labels = [
        ('Name',            U_('Name'),        25, 10, 100, wx.LIST_FORMAT_LEFT),
        ('State',           U_('State'),        4,  2,   8, wx.LIST_FORMAT_LEFT),
        ('Date',            U_('Date'),        12,  4,  20, wx.LIST_FORMAT_RIGHT),
        ('Rev',             U_('Rev'),          4,  2,   8, wx.LIST_FORMAT_RIGHT),
        ('Author',          U_('Author'),      10,  4,  80, wx.LIST_FORMAT_LEFT),
#       ('Size',            U_('Size'),         6,  4,  10, wx.LIST_FORMAT_RIGHT),
        ('Mimetype',        U_('Mimetype'),    10,  6,  50, wx.LIST_FORMAT_LEFT),
        ('EOL',             U_('EOL'),          6,  2,  10, wx.LIST_FORMAT_LEFT),
        ('Type',            U_('Type'),         4,  4,  10, wx.LIST_FORMAT_LEFT),
        ('Lock Owner',      U_('Lock Owner'),  10,  4,  80, wx.LIST_FORMAT_LEFT),
        ('Lock Comment',    U_('Lock Comment'),60, 10, 100, wx.LIST_FORMAT_LEFT),
        ]

class ColumnInfo:
    def __init__( self, col_id, name, label, width, min_width, max_width, alignment ):
        self.col_id = col_id
        self.name = name
        self.label = label
        self.width = int(width)
        self.min_width = int(min_width)
        self.max_width = int(max_width)
        self.alignment = alignment
        self.included = False
        self.column = 0

class ViewColumnInfo:
    def __init__( self ):
        self.column_info_by_name = {}
        self.column_info_by_id = {}
        self.column_order = []
        for col_id, col_info in enumerate( col_labels ):
            name, label, width, min_width, max_width, alignment = col_info
            ci = ColumnInfo( col_id, name, label, width, min_width, max_width, alignment )
            self.column_info_by_name[ name ] = ci
            self.column_info_by_id[ col_id ] = ci

    def setFromPreferenceData( self, p ):
        self.setFrom( p.column_order[:], p.column_widths[:] )

    def setFrom( self, column_order, column_widths ):
        # must have Name
        if 'Name' not in column_order:
            column_order.insert( 0, 'Name' )
            column_widths.insert( 0, '0' )

        for index, name in enumerate( column_order ):
            if self.column_info_by_name.has_key( name ):
                if len(column_widths) > index:
                    try:
                        width = int(column_widths[index])
                        info = self.column_info_by_name[ name ]
                        if( width >= info.min_width
                        and width <= info.max_width ):
                            info.width = width

                    except ValueError:
                        pass

        self.setColumnOrder( column_order )


    def getInfoByName( self, name ):
        return self.column_info_by_name[ name ]

    def getInfoById( self, col_id ):
        return self.column_info_by_id[ col_id ]

    def getNameById( self, col_id ):
        return self.column_info_by_id[ col_id ].name

    def excludedInfo( self ):
        return [info for info in self.column_info_by_name.values() if not info.included]

    def setColumnOrder( self, column_order ):
        self.column_order = column_order[:]
        for index, name in enumerate( self.column_order ):
            self.column_info_by_name[ name ].column = index

    def getColumnOrder( self ):
        return self.column_order

    def getNameByColumn( self, col ):
        return self.column_order[ col ]

    def getInfoByColumn( self, col ):
        return self.column_info_by_name[ self.column_order[ col ] ]

    def getColumnWidths( self ):
        return [str(self.column_info_by_name[name].width) for name in self.column_order]

class SubversionListHandlerCommon(wb_list_panel_common.ListHandler):
    col_name =          'Name'
    col_state =         'State'
    col_date =          'Date'
    col_revision =      'Rev'
    col_author =        'Author'
    col_type =          'Type'
    col_size =          'Size'
    col_mime_type =     'Mimetype'
    col_eol_style =     'EOL'
    col_lock_owner =    'Lock Owner'
    col_lock_comment =  'Lock Comment'

    def __init__( self, app, list_panel, project_info ):
        wb_list_panel_common.ListHandler.__init__( self, list_panel )
        self.project_info = project_info
        self.app = app

        self.all_files = []

        self.all_item_attr = {}

        self.column_info = ViewColumnInfo()
        self.need_properties = False

        self.is_project_parent = False

        self.__last_wc_path = None

        self.__branch_origin_revision = None
        self.__branch_url = None
        self.__branch_origin_url = None

    def setIsProjectParent( self ):
        self.is_project_parent = True

    def isProjectParent( self ):
        return self.is_project_parent

    def updateStatus( self ):
        try:
            self.project_info.updateStatus()
        except pysvn.ClientError, e:
            print 'Error: %s' % e.args[0]

    def getBackgroundColour( self ):
        return (255,255,255)

    def getBranchOriginRevision( self ):
        if self.__branch_origin_revision is None:
            try:
                log_entries = self.project_info.client_bg.log(self.project_info.url, discover_changed_paths=True)
            except pysvn.ClientError, e:
                self.app.log_client_error( e )
                return None

            branch_log_entry = log_entries[-1]
            changed_paths = branch_log_entry['changed_paths'][0]

            # If the oldest revision has a copyfrom_path, this is a branch,
            # so we set __branch_origin_url, __branch_url and __branch_origin_revision.
            if changed_paths['copyfrom_path'] is not None:
                base_url = '/'.join(self.project_info.url.split('/')[:4])
                self.__branch_origin_url = base_url + changed_paths['copyfrom_path']
                self.__branch_url = base_url + changed_paths['path']
                self.__branch_origin_revision = changed_paths['copyfrom_revision']

        return self.__branch_origin_revision

    def getBranchOriginUrl( self ):
        self.getBranchOriginRevision()
        return self.__branch_origin_url

    def getBranchUrl( self ):
        self.getBranchOriginRevision()
        return self.__branch_url

    def getProjectInfo( self ):
        return self.project_info

    def setupColumnInfo( self ):
        self.column_info.setFromPreferenceData( self.app.prefs.getView() )

    def setupColumns( self ):
        self.setupColumnInfo()

        g = self.list_panel.list_ctrl

        # should update in place in case the list was used by other code
        while g.GetColumnCount() > 0:
            g.DeleteColumn( 0 )

        need_properties = False

        char_width = 11
        for index, name in enumerate( self.column_info.getColumnOrder() ):
            info = self.column_info.getInfoByName( name )
            g.InsertColumn( index, T_(info.label), info.alignment, info.width*char_width )
            if name in [self.col_mime_type, self.col_eol_style]:
                need_properties = True

        self.project_info.setNeedProperties( need_properties )

    def initList( self, sort_data, filter_field, filter_text ):
        self.app.trace.info( 'SubversionListHandlerCommon.initList %s', self.project_info.project_name )

        g = self.list_panel.list_ctrl

        self.list_panel.updateHeader( self.project_info.url, self.project_info.wc_path )

        # nothing doing if the wc does not exist
        if self.project_info.need_checkout:
            # empty the list
            g.DeleteAllItems()

            self.__last_wc_path = None
            self.app.trace.info( 'initList no wc_path %s', self.project_info.project_name )
            g.SetItemCount( 1 )
            return

        self.app.log.debug( 'initList - last wc_path %r' % self.__last_wc_path )
        if self.__last_wc_path == self.project_info.wc_path:
            selection_state = self.__saveListSelectionState()
        else:
            self.app.log.debug( 'initList - changed wc_path to %r' % self.project_info.wc_path )
            selection_state = (None, [])

        self.__last_wc_path = self.project_info.wc_path

        # empty the list
        g.DeleteAllItems()

        prefix_len = len( self.project_info.wc_path ) + 1
        if len(filter_text) > 0:
            if filter_field ==  T_('Name'):
                self.all_files = [f for f in self.project_info.getFilesStatus()
                            if filter_text.lower() in f.path[prefix_len:].lower()]
            elif filter_field ==  T_('Author'):
                self.all_files = [f for f in self.project_info.getFilesStatus()
                            if f.entry is not None and filter_text.lower() in f.entry.commit_author.lower()]
        else:
            self.all_files = self.project_info.getFilesStatus()

        view_prefs = self.app.prefs.getView()
        if view_prefs.view_onlychanges:
            modified_states = [ pysvn.wc_status_kind.modified,
                                pysvn.wc_status_kind.added,
                                pysvn.wc_status_kind.deleted,
                                pysvn.wc_status_kind.conflicted,
                                ]
            af = self.all_files
            self.all_files = []
            for f in af:
                text_status = self.getTextStatus(f)
                prop_status = self.getPropStatus(f)
                if text_status in modified_states or prop_status in modified_states:
                    self.all_files.append( f )
                    
        self.all_files.sort( SortList( sort_data, self.project_info ) )

        self.__restoreListSelectionState( selection_state )

    def sortList( self, sort_data ):
        self.app.log.debug('sortList' )

        if self.project_info.need_checkout:
            # nothing to sort
            return

        selection_state = self.__saveListSelectionState()
        self.all_files.sort( SortList( sort_data, self.project_info ) )
        self.__restoreListSelectionState( selection_state )

        self.list_panel.list_ctrl.RefreshItems( 0, len(self.all_files)-1 )

    def __saveListSelectionState( self ):
        row = self.__focusedRow()
        if row is None:
            focused_filename = None
        else:
            focused_filename = self.getFilename( row )

        all_selected_filenames = [self.getFilename( row )
                                    for row in self.list_panel.getSelectedRows()]

        self.app.log.debug( '__saveListSelectionState %r %r' % (focused_filename, all_selected_filenames) )
        return (focused_filename, all_selected_filenames)

    def __restoreListSelectionState( self, (focused_filename, all_selected_filenames) ):
        g = self.list_panel.list_ctrl

        self.app.log.debug( '__restoreListSelectionState In %r %r' % (focused_filename, all_selected_filenames) )

        focused_index = 0
        g.SetItemCount( len(self.all_files) )
        for index, status in enumerate( self.all_files ):
            state = 0
            if status.path in all_selected_filenames:
                state = wx.LIST_STATE_SELECTED
            if focused_filename is not None and status.path == focused_filename:
                focused_index = index
                state |= wx.LIST_STATE_FOCUSED
            g.SetItemState( index, state, wx.LIST_STATE_SELECTED|wx.LIST_STATE_FOCUSED )

        if len(self.all_files) > 0:
            g.EnsureVisible( focused_index )

        self.app.log.debug( '__restoreListSelectionState Out %r' % (len(self.all_files),) )

    def __focusedRow( self ):
        g = self.list_panel.list_ctrl
        for index in range( len( self.all_files ) ):
            if g.GetItemState( index, wx.LIST_STATE_FOCUSED ) != 0:
                return index

        return None

    def columnRequired( self, col ):
        return self.column_info.getInfo( col ).included

    def columnIndex( self, col ):
        return self.column_info.getInfo( col ).column

    def getColumnId( self, col ):
        return self.column_info.getColumnOrder()[col]

    def _getNameColPrefix( self ):
        prefix_len = len( self.project_info.wc_path )
        if not self.project_info.wc_path.endswith( os.sep ):
            prefix_len += 1

        return prefix_len

    def OnGetItemText( self, index, col ):
        column = self.column_info.getNameByColumn( col )

        if self.project_info.need_checkout:
            if column == self.col_name:
                if self.isProjectParent():
                    return T_('Use the Checkout command to fetch files')
                else:
                    return T_('Use the Update command to fetch files')
            else:
                return ''

        status = self.all_files[ index ]

        if column == self.col_name:
            value = self.__get_NameColumn( status, self._getNameColPrefix() )

        elif column == self.col_state:
            value = self.__get_StateColumn( status )

        elif column == self.col_date:
            value = self.__get_DateColumn( status )

        elif column == self.col_revision:
            value = self.__get_RevisionColumn( status )

        elif column == self.col_author:
            value = self.__get_AuthorColumn( status )

        elif column == self.col_type:
            value = self.__get_TypeColumn( status )

        elif column == self.col_size:
            value = self.__get_SizeColumn( status )

        elif column == self.col_mime_type:
            value = self.__get_MimeTypeColumn( self.project_info.getProperty( status.path, 'svn:mime-type' ) )

        elif column == self.col_eol_style:
            value = self.__get_EolStyleColumn( self.project_info.getProperty( status.path, 'svn:eol-style' ) )

        elif column == self.col_lock_owner:
            value = self.__get_LockOwnerColumn( status )

        elif column == self.col_lock_comment:
            value = self.__get_LockCommentColumn( status )

        else:
            value = 'Opss'

        return value

    def OnGetItemAttr( self, index ):
        if self.project_info.need_checkout:
            colour = wb_config.colour_status_need_checkout
        else:
            colour = self.statusColour( self.all_files[ index ] )

        if colour not in self.all_item_attr:
            attr = wx.ListItemAttr()
            attr.SetTextColour( colour )
            self.all_item_attr[ colour ] = attr

        return self.all_item_attr[ colour ]

    def isItemImageFolder(self, item):
        if self.project_info.need_checkout:
            return True

        elif self.GetItemIsDir( item ):
            return True

        else:
            return False

    def GetItemIsDir(self, item):
        #FIXME: turnaround solution, use a default one instead of False?
        try:
            status = self.all_files[ item ]
        except:
            return False
        if status.entry is None:
            is_dir = os.path.isdir( status.path )
        else:
            is_dir = status.entry.kind == pysvn.node_kind.dir
        return is_dir
    
    def __get_NameColumn( self, status, prefix_len ):
        if status.entry is None:
            is_dir = os.path.isdir( status.path )
        else:
            is_dir = status.entry.kind == pysvn.node_kind.dir
        if is_dir:
            filename = status.path + os.sep
        else:
            filename = status.path

        return filename[prefix_len:]

    def __get_SizeColumn( self, status ):
        type( status )
        return '%d' % 0

    def __get_EolStyleColumn( self, value ):
        if value is None:
            value = ''

        return value

    def __get_MimeTypeColumn( self, value ):
        if value is None:
            value = ''

        return value

    def __get_StateColumn( self, status ):
        if status.path in self.getAllGreyFilenames():
            return '--'

        return self.statusFormatString( status )

    def __get_TypeColumn( self, status ):
        if status.entry is None:
            return ''
        else:
            return str(status.entry.kind)

    def __get_AuthorColumn( self, status ):
        if status.entry is None or status.entry.commit_author is None:
            return ''
        else:
            return status.entry.commit_author

    def __get_RevisionColumn( self, status ):
        if status.entry is None or status.entry.commit_revision.number < 0:
            return ''
        else:
            return str(status.entry.commit_revision.number)

    def __get_DateColumn( self, status ):
        if status.entry is None or status.entry.commit_time == 0:
            return ''
        else:
            return wb_subversion_utils.fmtDateTime( status.entry.commit_time )

    def __get_LockCommentColumn( self, status ):
        if status.repos_lock is not None:
            comment = status.repos_lock.comment.replace( '\n', ' ' )
        elif status.entry is not None and status.entry.lock_comment is not None:
            comment = status.entry.lock_comment.replace( '\n', ' ' )
        else:
            comment = ''
        return comment

    def __get_LockOwnerColumn( self, status ):
        if status.repos_lock is not None:
            owner = status.repos_lock.owner
        elif status.entry is not None and status.entry.lock_owner is not None:
            owner = status.entry.lock_owner
        else:
            owner = ''
        return owner

    def getState( self, all_rows ):
        if len(all_rows) == 0:
            return None

        state = wb_list_panel_common.ListItemState()

        if self.project_info.need_checkout:
            state.need_checkout = True
            state.ui_project_parent = True
            state.versioned = True
            return state

        state.modified = True
        state.new_versioned = True
        state.versioned = True
        state.unversioned = True
        state.need_checkin = True
        state.conflict = True
        state.file_exists = True
        state.is_folder = True
        state.revertable = True

        for row in all_rows:
            filename = self.all_files[ row ].path

            if not os.path.exists( filename ):
                state.file_exists = False

            if os.path.isdir( filename ):
                state.modified = False
                state.conflict = False
                state.file_exists = False
                state.revertable = False
            else:
                state.is_folder = False

            text_status = self.getTextStatus( row )
            if text_status in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
                state.versioned = False

            if text_status not in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
                state.unversioned = False

            if text_status not in [pysvn.wc_status_kind.added]:
                state.new_versioned = False

            prop_status = self.getPropStatus( row )
            if( text_status not in [pysvn.wc_status_kind.modified
                                   ,pysvn.wc_status_kind.conflicted]
            and prop_status not in [pysvn.wc_status_kind.modified
                                   ,pysvn.wc_status_kind.conflicted] ):
                state.modified = False

            if( text_status not in [pysvn.wc_status_kind.added
                                   ,pysvn.wc_status_kind.deleted
                                   ,pysvn.wc_status_kind.replaced
                                   ,pysvn.wc_status_kind.modified]
            and prop_status not in [pysvn.wc_status_kind.added
                                   ,pysvn.wc_status_kind.deleted
                                   ,pysvn.wc_status_kind.replaced
                                   ,pysvn.wc_status_kind.modified] ):
                state.need_checkin = False

            if text_status not in [pysvn.wc_status_kind.conflicted]:
                state.conflict = False

            # revertable status calculation
            text_reverable = (text_status in [pysvn.wc_status_kind.added
                                             ,pysvn.wc_status_kind.deleted
                                             ,pysvn.wc_status_kind.missing
                                             ,pysvn.wc_status_kind.replaced
                                             ,pysvn.wc_status_kind.modified
                                             ,pysvn.wc_status_kind.conflicted])
            prop_revertable = (prop_status in [pysvn.wc_status_kind.modified
                                              ,pysvn.wc_status_kind.deleted
                                              ,pysvn.wc_status_kind.replaced
                                              ,pysvn.wc_status_kind.conflicted])

            if not text_reverable and not prop_revertable:
                state.revertable = False

        #state.printState( 'getState' )

        return state

    def getStatusFromRowOrStatus( self, row_or_status ):
        if type(row_or_status) == types.IntType:
            return self.all_files[ row_or_status ]
        return row_or_status

    def mayOpen( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        if status.entry is None:
            return not os.path.isdir( self.getFilename( row_or_status ) )
        else:
            return status.entry.kind == pysvn.node_kind.dir

    def getFilename( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.path

    def getStatusString( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return wb_subversion_utils._status_format( status )

    def getStatusAndFilenames( self, all_rows ):
        return [(self.getStatusString( row_or_status ), self.getFilename( row_or_status )) for row_or_status in all_rows]

    def isControlled( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.entry is not None

    def getUrl( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        if status.entry is None:
            return ''
        else:
            return status.entry.url

    def getConflictOld( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        if status.entry is None:
            return ''
        else:
            return os.path.join( os.path.dirname( status.path ), status.entry.conflict_old )

    def getConflictNew( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        if status.entry is None:
            return ''
        else:
            return os.path.join( os.path.dirname( status.path ), status.entry.conflict_new )

    def getConflictMine( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        if status.entry is None:
            return ''
        else:
            return os.path.join( os.path.dirname( status.path ), status.entry.conflict_work )

    def getTextStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.text_status

    def getPropStatus( self, row_or_status ):
        status = self.getStatusFromRowOrStatus( row_or_status )
        return status.prop_status

    def statusFormatString( self, status ):
        return wb_subversion_utils._status_format( status )

    def getAllGreyFilenames( self ):
        raise NotImplementedError

    def statusColour( self, status ):
        # default colour when nothing special is know for the file
        colour = wb_config.colour_status_normal

        # show that a file is on the clipboard
        if status.path in self.getAllGreyFilenames():
            colour = wb_config.colour_status_disabled

        # show that a file is uncontrolled
        elif status.entry is None:
            colour = wb_config.colour_status_unversioned

        else:
            # show a file is locked
            if( status.is_locked ):
                colour = wb_config.colour_status_locked
            # show a file is modified
            elif( self.getTextStatus( status ) != pysvn.wc_status_kind.normal
            or self.getPropStatus( status ) not in [pysvn.wc_status_kind.normal,pysvn.wc_status_kind.none]
            or status.is_copied or status.is_switched ):
                colour = wb_config.colour_status_modified

        return colour

    #------------------------------------------------------------
    def Cmd_File_Annotate( self, all_rows ):
        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setProgress( T_('Annotating %(count)d'), 0 )

            self.app.setAction( T_('Annotate %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                annotation = self.project_info.client_bg.annotate( filename )
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

    def Cmd_File_DiffWorkBase( self, all_rows ):
        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setAction( T_('Diff BASE %s...') % filename )

            info1 = wb_subversion_diff.PathInfoForDiff()

            info1.path = filename
            info1.revision = pysvn.Revision( pysvn.opt_revision_kind.base )
            info1.title = filename + '@BASE'

            info2 = wb_subversion_diff.PathInfoForDiff()

            info2.path = filename
            info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
            info2.title = filename

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

    def Cmd_File_DiffWorkHead( self, all_rows ):
        for filename, url in [(self.getFilename( row ), self.getUrl( row ))
                                for row in all_rows]:

            self.app.setAction( T_('Diff HEAD %s...') % filename )

            info1 = wb_subversion_diff.PathInfoForDiff()

            info1.path = filename
            info1.revision = pysvn.Revision( pysvn.opt_revision_kind.head )
            info1.title = filename + '@HEAD'

            info2 = wb_subversion_diff.PathInfoForDiff()

            info2.path = filename
            info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
            info2.title = filename

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

    def Cmd_File_DiffWorkBranchOriginBase( self, all_rows ):
        self.app.setAction( T_("Retrieving branch info...") )

        yield self.app.backgroundProcess
        branch_url = self.getBranchUrl()
        yield self.app.foregroundProcess

        if branch_url is None:
            wx.MessageBox( T_('"%s" is not a branch.') % self.project_info.url, T_("Error"), style=wx.OK|wx.ICON_ERROR )
        else:
            branch_origin_url = self.getBranchOriginUrl()

            for filename, url in [(self.getFilename( row ), self.getUrl( row ))
                                    for row in all_rows]:
                origin_url = branch_origin_url + url[len(branch_url):]

                self.app.setAction( T_('Diff branch origin BASE %s...') % filename )

                info1 = wb_subversion_diff.PathInfoForDiff()

                info1.path = origin_url
                info1.revision = self.getBranchOriginRevision()
                info1.title = '%s@%d' % (filename, self.getBranchOriginRevision().number)

                info2 = wb_subversion_diff.PathInfoForDiff()

                info2.path = filename
                info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
                info2.title = filename

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

    def Cmd_File_DiffWorkBranchOriginHead( self, all_rows ):
        self.app.setAction( T_("Retrieving branch info...") )
        yield self.app.backgroundProcess
        branch_url = self.getBranchUrl()
        yield self.app.foregroundProcess

        if branch_url is None:
            wx.MessageBox( T_('"%s" is not a branch.') % self.project_info.url, T_("Error"), style=wx.OK|wx.ICON_ERROR )
        else:
            branch_origin_url = self.getBranchOriginUrl()

            for filename, url in [(self.getFilename( row ), self.getUrl( row ))
                                    for row in all_rows]:
                origin_url = branch_origin_url + url[len(branch_url):]

                self.app.setAction( T_('Diff branch origin HEAD %s...') % filename )

                info1 = wb_subversion_diff.PathInfoForDiff()

                info1.path = origin_url
                info1.revision = pysvn.Revision( pysvn.opt_revision_kind.head )
                info1.title = '%s@HEAD' % filename

                info2 = wb_subversion_diff.PathInfoForDiff()

                info2.path = filename
                info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
                info2.title = filename

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

    def Cmd_File_History( self, all_rows ):
        dialog = wb_subversion_history.LogHistoryDialog( self.app, self.app.frame.tree_panel.tree_ctrl )
        result = dialog.ShowModal()
        if result != wx.ID_OK:
            return

        for filename in [self.getFilename( row ) for row in all_rows]:
            self.app.setAction( T_('Log history %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
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

            if not ok:
                break

            h_frame = wb_subversion_history.HistoryFileFrame(
                        self.app,
                        self.project_info,
                        filename,
                        file_url,
                        history_entries )
            h_frame.Show( True )

        self.app.setAction( T_('Ready') )

    def Cmd_File_Info( self, all_rows ):
        for filename in [self.getFilename( row ) for row in all_rows]:
            try:
                if hasattr( self.project_info.client_fg, 'info2' ):
                    entry = self.project_info.client_fg.info2( filename, recurse=False )
                else:
                    entry = self.project_info.client_fg.info( filename )

                dialog = wb_subversion_info_dialog.InfoDialog( self.app,
                        self.list_panel.list_ctrl,
                        filename,
                        entry )
                dialog.ShowModal()

            except pysvn.ClientError, e:
                self.app.log_client_error( e )

    def Cmd_File_Lock( self, all_rows ):
        all_filenames = [self.getFilename( row ) for row in all_rows]
        comment, force = self.app.getLockMessage( T_('Lock'), self.getStatusAndFilenames( all_rows ) )
        if not comment:
            return

        for filename in all_filenames:
            self.app.setProgress( T_('Locking %(count)d'), 0 )

            self.app.setAction( T_('Locking %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                self.project_info.client_bg.lock( filename, comment=comment, force=force )
                ok = True
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_File_Properties( self, all_rows ):
        client_fg = self.project_info.client_fg

        for filename in [self.getFilename( row ) for row in all_rows]:
            try:
                prop_list = client_fg.proplist( filename,
                        revision=pysvn.Revision( pysvn.opt_revision_kind.working ) )
                if len(prop_list) == 0:
                    prop_dict = {}
                else:
                    _, prop_dict = prop_list[0]
                if os.path.isdir( filename ):
                    dialog = wb_subversion_properties_dialog.DirPropertiesDialog( self.app,
                            self.list_panel.list_ctrl,
                            filename,
                            prop_dict )
                else:
                    dialog = wb_subversion_properties_dialog.FilePropertiesDialog( self.app,
                            self.list_panel.list_ctrl,
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
                break
            self.app.refreshFrame()

    def Cmd_File_Unlock( self, all_rows ):
        confirmed, force = self.app.confirmForceAction( T_('Unlock'), self.getStatusAndFilenames( all_rows ) )
        if not confirmed:
            return

        for filename, url in [(self.getFilename( row ), self.getUrl( row )) for row in all_rows]:
            self.app.setProgress( T_('Unlocking %(count)d'), 0 )

            self.app.setAction( T_('Unlocking %s...') % filename )

            yield self.app.backgroundProcess

            ok = False
            try:
                if force:
                    self.project_info.client_bg.unlock( url, force=True )
                else:
                    self.project_info.client_bg.unlock( filename, force=False )
                ok = True
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

            if not ok:
                break

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

class SortList:
    def __init__( self, sort_data, project_info ):
        self.sort_data = sort_data
        self.project_info = project_info

    def __call__( self, a, b ):
        # called to cmp
        a_field = self.getField( a, self.sort_data.getField() )
        b_field = self.getField( b, self.sort_data.getField() )
        ordering = cmp( a_field, b_field )
        if ordering == 0:
            a_path = self.getField( a, SubversionListHandlerCommon.col_name )
            b_path = self.getField( b, SubversionListHandlerCommon.col_name )
            ordering = cmp( a_path, b_path )
            return ordering
        else:
            return ordering * self.sort_data.getOrder()

    def getField( self, status, field ):
        __pychecker__ = '--no-returnvalues'

        if field == SubversionListHandlerCommon.col_name:
            return status.path.lower()

        if field == SubversionListHandlerCommon.col_state:
            # Use positive text_status first
            # then positive prop_status
            # other wise use negative text_status
            text_val = wb_subversion_utils.wc_status_kind_text_sort_map[ status.text_status ]
            if text_val > 0:
                return text_val

            prop_val = wb_subversion_utils.wc_status_kind_text_sort_map[ status.prop_status ]
            if prop_val > 0:
                return prop_val + wb_subversion_utils.prop_sort_offset

            if text_val < 0:
                return -text_val

            if self.sort_data.getOrder():
                return 999
            else:
                return 0

        if field == SubversionListHandlerCommon.col_revision:
            if status.entry is None or status.entry.commit_revision.number == 0:
                if self.sort_data.getOrder() > 0:
                    return 9999999
                else:
                    return 0
            else:
                return status.entry.commit_revision.number
        if field == SubversionListHandlerCommon.col_author:
            if status.entry is None or status.entry.commit_author is None:
                if self.sort_data.getOrder() > 0:
                    return (1, u'')
                else:
                    return (-1, u'')
            else:
                return (0, status.entry.commit_author)

        if field == SubversionListHandlerCommon.col_date:
            if status.entry is None:
                return 0
            else:
                return status.entry.commit_time

        if field == SubversionListHandlerCommon.col_type:
            if status.entry is None:
                return pysvn.node_kind.none
            else:
                return status.entry.kind


        if field == SubversionListHandlerCommon.col_eol_style:
            value = self.project_info.getProperty( status.path, 'svn:eol-style' )
            if value in ['', None]:
                if self.sort_data.getOrder() > 0:
                    value = (1, u'')
                else:
                    value = (-1, u'')
            else:
                value = (0, value)

            return value

        if field == SubversionListHandlerCommon.col_mime_type:
            return self.project_info.getProperty( status.path, 'svn:mime-type' )

        if field == SubversionListHandlerCommon.col_lock_owner:
            if status.repos_lock is not None:
                value = status.repos_lock.owner
            elif status.entry is not None:
                value = status.entry.lock_owner
            else:
                value = u''

            if value in ['', None]:
                if self.sort_data.getOrder() > 0:
                    value = (1, u'')
                else:
                    value = (-1, u'')
            else:
                value = (0, value)

            return value

        if field == SubversionListHandlerCommon.col_lock_comment:
            if status.repos_lock is not None:
                value = status.repos_lock.comment.replace( '\n', ' ' )
            elif status.entry is not None and status.entry.lock_comment is not None:
                value = status.entry.lock_comment.replace( '\n', ' ' )
            else:
                value = u''

            if value in ['', None]:
                if self.sort_data.getOrder() > 0:
                    value = (1, u'')
                else:
                    value = (-1, u'')
            else:
                value = (0, value)

            return value

        raise wb_exceptions.InternalError( 'SortList does not support field %s' % field )

class SortListCtrl(SortList):
    def __init__( self, all_files, sort_data, project_info ):
        SortList.__init__( self, sort_data, project_info )
        self.all_files = all_files

    def getField( self, index, field ):
        return SortList.getField( self, self.all_files[index], field )
