'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_history.py

'''
import wx
import wx.lib.splitter
import wx.calendar

import os
import time
import types

import pysvn

import wb_images
import wb_subversion_utils
import wb_subversion_diff
import wb_subversion_annotate
import wb_config

id_view_cmd = wx.NewId()
id_diff_cmd = wx.NewId()
id_annotate_cmd = wx.NewId()
id_revision_changes_cmd = wx.NewId()
id_list = wx.NewId()
id_paths = wx.NewId()

action_map = {
    'A': 'Add',
    'D': 'Delete',
    'M': 'Modified',
    }

class LogEntry:
    def __init__( self,
            rev_number,
            url,
            author,
            date,
            label,
            message,
            changed_paths ):
        self.rev_number = rev_number
        self.url = url
        self.author = author
        self.date = date
        self.label = label
        self.message = message
        self.changed_paths = changed_paths

        self.changed_paths.sort( self.by_changed_path )

    def by_changed_path( self, a, b ):
        return cmp( a.path, b.path )

    def matchFilter( self, filter_field, filter_text ):
        if filter_text == '':
            return True

        if self.label != '':
            return True

        if filter_field == T_('Author'):
            return filter_text.lower() in self.author.lower()
        elif filter_field == T_('Comment'):
            return filter_text.lower() in self.message.lower()
        elif filter_field == T_('Path'):
            for changed_path in self.changed_paths:
                if filter_text.lower() in changed_path.path.lower():
                    return True

            return False
        else:
            assert( False )
            return False

def getHistoryEntries( project_info, filename, limit, revision_end, include_tags ):
    all_history_entries = []
    # need the URL and repos_root_URL
    # [0] first entry [0][1] the info
    info = project_info.client_bg.info2( filename, recurse=False )[0][1]
    if info.repos_root_URL is None:
        info = project_info.client_bg.info2( info.URL, recurse=False )[0][1]

    all_log_entries = project_info.client_bg.log(
                    filename,
                    strict_node_history=False,
                    discover_changed_paths=True,
                    limit=limit,
                    revision_end=revision_end )

    # Settings an end date can lead to no entries
    if len( all_log_entries ) == 0:
        return info.URL, all_history_entries

    repos_path = info.URL[len(info.repos_root_URL):]
    for log in all_log_entries:
        # author is optional
        if 'author' not in log:
            log.author = ''

        all_history_entries.append(
            LogEntry(
                log.revision.number,
                info.repos_root_URL+repos_path,
                log.author,
                log.date,
                '',
                log.message,
                log.changed_paths ) )

        for changed_path in log.changed_paths:
            if changed_path.action in ['A','M']:
                if repos_path == changed_path.path:
                    if changed_path.copyfrom_path is not None:
                        repos_path = changed_path.copyfrom_path
                    break

    all_history_entries.sort( __cmpLogEntryHighToLow )

    oldest_rev = log.revision.number

    tags_url = project_info.getTagsUrl( info.URL )
    if include_tags and tags_url:
        try:
            tag_info = project_info.client_bg.info2( tags_url, recurse=False )
            tag_repos_prefix = tags_url[len(tag_info[0][1].repos_root_URL):]
            all_tag_names = set()

            for log in project_info.client_bg.log( tags_url, discover_changed_paths=True ):
                # author is optional
                if 'author' not in log:
                    log.author = ''

                for changed_path in log.changed_paths:
                    if( changed_path.copyfrom_revision is not None
                    # only include if it has taged an item in the history
                    and changed_path.copyfrom_revision.number > oldest_rev ):
                        tag_suffix = changed_path.path[len(tag_repos_prefix)+1:]
                        tag_name = tag_suffix.split('/')[0]

                        if tag_name not in all_tag_names:
                            all_history_entries.append(
                                LogEntry(
                                    changed_path.copyfrom_revision.number,
                                    __findTaggedUrl( all_history_entries, changed_path.copyfrom_revision.number ),
                                    log.author,
                                    log.date,
                                    'Tag ' + tag_name,
                                    log.message,
                                    log.changed_paths) )

                        all_tag_names.add( tag_name )
                        break

        except pysvn.ClientError, e:
            print 'Cannot find tags in %s - %s' % (tags_url, str(e))

    all_history_entries.sort( __cmpLogEntryHighToLow )
    return info.URL, all_history_entries

def __cmpLogEntryHighToLow( a, b ):
    return -cmp( a.rev_number, b.rev_number )

def __findTaggedUrl( all_history_entries, tag_revnum ):
    for entry in all_history_entries:
        if entry.rev_number < tag_revnum:
            return entry.url

    # this cannot happen
    raise RuntimeError( '__findTaggedUrl failed to find tagged url' )

class LogHistoryDialog(wx.Dialog):
    def __init__( self, app, parent ):
        wx.Dialog.__init__( self, parent, -1, T_('Log History') )

        p = app.prefs.getLogHistory()

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        is_show_all = p.default_mode == 'show_all'
        is_show_limit = p.default_mode == 'show_limit'
        is_show_since = p.default_mode == 'show_since'

        self.all_radio = wx.RadioButton( self, -1, T_('Show all entries') )
        self.all_radio.SetValue( is_show_all )

        self.g_sizer.Add( self.all_radio, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( (0,0), 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.limit_radio = wx.RadioButton( self, -1, T_('Show only:') )
        self.limit_radio.SetValue( is_show_limit )
        self.limit_text = wx.TextCtrl( self, -1, str(p.default_limit), style=wx.TE_RIGHT )
        self.limit_text.Enable( is_show_limit )

        self.g_sizer.Add( self.limit_radio, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.limit_text, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.date = wx.DateTime_Now()
        self.date.SubtractDS( wx.DateSpan( days=p.default_since_days_interval ) )

        self.since_radio = wx.RadioButton( self, -1, T_('Show since:') )
        self.since_radio.SetValue( is_show_since )
        self.since_date = wx.calendar.CalendarCtrl( self, -1,
                                self.date,
                                style=wx.calendar.CAL_MONDAY_FIRST )
        self.since_date.Enable( is_show_since )

        self.g_sizer.Add( self.since_radio, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_TOP, 3 )
        self.g_sizer.Add( self.since_date, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.tags_label = wx.StaticText( self, -1, T_('Include tags: '), style=wx.ALIGN_RIGHT)
        self.tags_ctrl = wx.CheckBox( self, -1, T_('Include tags in log history') )
        self.tags_ctrl.SetValue( p.default_include_tags )

        self.g_sizer.Add( self.tags_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.g_sizer.Add( self.tags_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.g_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

        wx.EVT_RADIOBUTTON( self, self.all_radio.GetId(), self.OnRadio )
        wx.EVT_RADIOBUTTON( self, self.limit_radio.GetId(), self.OnRadio )
        wx.EVT_RADIOBUTTON( self, self.since_radio.GetId(), self.OnRadio )

        wx.calendar.EVT_CALENDAR_SEL_CHANGED( self, self.since_date.GetId(), self.OnCalendarSelChanged )

    # ----------------------------------------
    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    # ----------------------------------------
    def OnRadio( self, event ):
        self.since_date.Enable( self.since_radio.GetValue() )
        self.limit_text.Enable( self.limit_radio.GetValue() )

    def OnCalendarSelChanged( self, event ):
        if self.since_radio.GetValue():
            # ensure that the date stays in the past
            date = self.since_date.GetDate()
            # sometimes the event is sent with a bogus value for the date
            # just ignore these events
            if date.GetTicks() == ((2**32)-1):
                return
            if date.IsLaterThan( wx.DateTime_Now() ):
                self.since_date.SetDate( self.date )
            else:
                self.date = self.copyDataTime( date )
        else:
            # CalendarCtrl does not disable day changes
            # force date back to self.date
            self.since_date.SetDate( self.date )

    def copyDataTime( self, date ):
        t = date.GetTicks()
        return wx.DateTimeFromTimeT( t )

    # ----------------------------------------
    def getLimit( self ):
        if self.limit_radio.GetValue():
            try:
                return int( self.limit_text.GetValue().strip() )
            except ValueError:
                return 10
        else:
            return 0

    def getRevisionEnd( self ):
        if self.since_radio.GetValue():
            date = self.since_date.GetDate()
            return pysvn.Revision( pysvn.opt_revision_kind.date, date.GetTicks() )
        else:
            return pysvn.Revision( pysvn.opt_revision_kind.number, 0 )

    def getIncludeTags( self ):
        return self.tags_ctrl.GetValue()

class HistoryFileFrame(wx.Frame):
    def __init__( self, app, project_info, filename, url, all_log_entries ):
        wx.Frame.__init__( self, None, -1, T_("History of %s") % filename, size=(700,500) )

        self.panel = LogHistoryPanel( self, app, project_info, filename, url, all_log_entries )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

    def OnCloseWindow( self, event ):
        self.Destroy()

    def diffFunction( self, app, project_info, info1, info2 ):
        return wb_subversion_diff.subversionDiffFiles(
                    app, project_info,
                    info1, info2 )

class HistoryDirFrame(wx.Frame):
    def __init__( self, app, project_info, filename, url, all_log_entries ):
        wx.Frame.__init__( self, None, -1, T_("History of %s") % filename, size=(700,500) )

        self.panel = LogHistoryPanel( self, app, project_info, filename, url, all_log_entries )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

    def OnCloseWindow( self, event ):
        self.Destroy()

    def diffFunction( self, app, project_info, info1, info2 ):
        return wb_subversion_diff.subversionDiffDir(
                    app, project_info,
                    info1, info2 )


class WbHistoryListCtrl(wx.ListCtrl):
    def __init__( self, parent, log_history, list_id ):
        wx.ListCtrl.__init__( self, parent, list_id,
                                style=wx.LC_REPORT|wx.NO_BORDER|wx.LC_HRULES|wx.LC_VIRTUAL )
        self.log_history = log_history

    def OnGetItemText(self, item, col):
        return self.log_history.OnGetItemText( item, col )

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        return self.log_history.OnGetItemAttr( item )

class PanelFilter(wx.Panel):
    def __init__( self, parent, app, filter_field ):
        wx.Panel.__init__(self, parent, -1)

        self.app = app

        self.background_colour = wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DFACE )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer2 = wx.BoxSizer( wx.HORIZONTAL )

        self.filter_changed_handler = None

        self.filter_field_choices = [ T_('Author'), T_('Comment'), T_('Path') ]
        self.filter_choice_ctrl = wx.Choice( self, wx.NewId(), choices=self.filter_field_choices )
        self.filter_choice_ctrl.SetSelection( self.filter_field_choices.index( filter_field ) )
        if wx.Platform == '__WXMAC__':
            self.filter_text_ctrl = wx.TextCtrl( self, wx.NewId(), '', size=(-1,-1) )
        else:
            self.filter_text_ctrl = wx.TextCtrl( self, wx.NewId(), '', size=(-1,10) )
        self.filter_clear_button = wx.Button( self, wx.NewId(), 'X', style=wx.BU_EXACTFIT, size=(30, -1) )

        border = 1
        self.h_sizer2.Add( self.filter_choice_ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border )
        if wx.Platform == '__WXMAC__':
            self.h_sizer2.Add( self.filter_text_ctrl, 1, wx.EXPAND|wx.ALL, border )
        else:
            self.h_sizer2.Add( self.filter_text_ctrl, 1, wx.EXPAND|wx.ALL, border+2 )
        self.h_sizer2.Add( self.filter_clear_button, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border )

        border = 3
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

class LogHistoryPanel:
    col_revision = 0
    col_author = 1
    col_date = 2
    col_label = 3
    col_message = 4

    col_action = 0
    col_path = 1
    col_copyfrom_revision = 2
    col_copyfrom_path = 3

    def __init__( self, parent, app, project_info, filename, url, all_log_entries ):
        self.parent = parent
        self.app = app
        self.project_info = project_info
        self.filename = filename
        self.url = url
        self.all_log_entries = all_log_entries

        # run from recent to old
        self.all_log_entries.sort( self.by_rev )

        self.filter_field = T_('Comment')
        self.filter_text = ''
        self.all_filtered_log_entries = all_log_entries

        # Create the splitter windows
        self.splitter = wx.lib.splitter.MultiSplitterWindow( parent )
        self.splitter.SetOrientation( wx.VERTICAL )

        # Make sure the splitters can't be removed by setting a minimum size
        self.splitter.SetMinimumPaneSize( 100 )

        # create the individule panels
        self.panel_history = wx.Panel( self.splitter, -1 )

        self.panel_comment = wx.Panel( self.splitter, -1 )
        self.panel_changed_paths = wx.Panel( self.splitter, -1 )

        # Arrange the panels with the splitter windows
        self.splitter.AppendWindow( self.panel_history, 250 )
        self.splitter.AppendWindow( self.panel_comment, 100 )
        self.splitter.AppendWindow( self.panel_changed_paths, 150 )

        self.selected_revisions = {}

        self.v_sizer_history = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer_comment = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer_changed_paths = wx.BoxSizer( wx.VERTICAL )

        self.panel_filter = PanelFilter( self.panel_history, app, self.filter_field )
        self.panel_filter.setFilterChangedHandler( self.OnFilterChanged )

        self.list_ctrl = WbHistoryListCtrl( self.panel_history, self, id_list )
        self.list_ctrl.SetFocus()
        self.all_item_attr = {}

        self.list_ctrl.InsertColumn( self.col_revision, T_("Revision") )
        self.list_ctrl.InsertColumn( self.col_author, T_("Author") )
        self.list_ctrl.InsertColumn( self.col_date, T_("Date") )
        self.list_ctrl.InsertColumn( self.col_label, T_("Label") )
        self.list_ctrl.InsertColumn( self.col_message, T_("Message") )

        char_width = 9
        self.list_ctrl.SetColumnWidth( self.col_revision, 7*char_width )
        self.list_ctrl.SetColumnWidth( self.col_author, 14*char_width )
        self.list_ctrl.SetColumnWidth( self.col_date, 15*char_width )
        self.list_ctrl.SetColumnWidth( self.col_label, 12*char_width )
        self.list_ctrl.SetColumnWidth( self.col_message, 40*char_width )

        # don't make the ctrl readonly as that prevents copy as well as insert
        self.comment_ctrl = wx.TextCtrl( self.panel_comment, -1, '', size=wx.Size(-1, -1), style=wx.TE_MULTILINE )
        self.comment_ctrl.SetInsertionPoint( 0 )

        self.paths_ctrl = wx.ListCtrl( self.panel_changed_paths, id_paths, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT|wx.NO_BORDER)

        self.paths_ctrl.InsertColumn( self.col_action, T_("Action") )
        self.paths_ctrl.InsertColumn( self.col_path, T_("Path") )
        self.paths_ctrl.InsertColumn( self.col_copyfrom_revision, T_("Copied Revision") )
        self.paths_ctrl.InsertColumn( self.col_copyfrom_path, T_("Copied from") )

        char_width = 9
        self.paths_ctrl.SetColumnWidth( self.col_action, 7*char_width )
        self.paths_ctrl.SetColumnWidth( self.col_path, 40*char_width )
        self.paths_ctrl.SetColumnWidth( self.col_copyfrom_revision, 6*char_width )
        self.paths_ctrl.SetColumnWidth( self.col_copyfrom_path, 40*char_width )

        self.initButtons( self.v_sizer_history )

        self.comment_label = wx.StaticText( self.panel_comment, -1, T_('Comment') )

        self.paths_label = wx.StaticText( self.panel_changed_paths, -1, T_('Changed Paths') )

        self.v_sizer_history.Add( self.panel_filter, 0, wx.EXPAND|wx.ALL, 0 )
        self.v_sizer_history.Add( self.list_ctrl, 2, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer_comment.Add( self.comment_label, 0, wx.ALL, 5 )
        self.v_sizer_comment.Add( self.comment_ctrl, 2, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer_changed_paths.Add( self.paths_label, 0, wx.ALL, 5 )
        self.v_sizer_changed_paths.Add( self.paths_ctrl, 2, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_LIST_ITEM_SELECTED( self.panel_history, id_list, self.OnListItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self.panel_history, id_list, self.OnListItemDeselected )

        wx.EVT_LIST_ITEM_SELECTED( self.panel_history, id_paths, self.OnPathItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self.panel_history, id_paths, self.OnPathItemDeselected )

        self.initList()

        wx.EVT_SIZE( self.panel_history, self.OnSizeHistory )
        wx.EVT_SIZE( self.panel_comment, self.OnSizeComment )
        wx.EVT_SIZE( self.panel_changed_paths, self.OnSizeChangedPaths )

        for panel, sizer in [
            (self.panel_history, self.v_sizer_history),
            (self.panel_comment, self.v_sizer_comment),
            (self.panel_changed_paths, self.v_sizer_changed_paths)]:

                panel.SetAutoLayout( True )
                panel.SetSizer( sizer )
                sizer.Fit( panel )
                panel.Layout()

    # ----------------------------------------
    def setFocusFilter( self ):
        self.panel_filter.setFocusFilter()

    def OnFilterChanged( self, field, text ):
        self.filter_field = field
        self.filter_text = text

        if self.filter_text == '':
            self.all_filtered_log_entries = self.all_log_entries
        else:
            self.all_filtered_log_entries = [
                log_entry for log_entry in self.all_log_entries
                    if log_entry.matchFilter( self.filter_field, self.filter_text )]

        self.initList()

    def OnGetItemText( self, index, col ):
        log_entry = self.all_filtered_log_entries[ index ]
        if col == self.col_revision:
            return str(log_entry.rev_number)
        elif col == self.col_author:
            return log_entry.author
        elif col ==  self.col_date:
            return wb_subversion_utils.fmtDateTime( log_entry.date )
        elif col ==  self.col_label:
            return log_entry.label
        elif col ==  self.col_message:
            return log_entry.message.replace( '\n', ' ' )
        else:
            assert( False )

    def OnGetItemImage( self, index ):
        return -1

    def OnGetItemAttr( self, index ):
        log_entry = self.all_filtered_log_entries[ index ]
        if len(log_entry.label) == 0:
            colour = wb_config.colour_log_normal
        else:
            colour = wb_config.colour_log_tag

        if colour not in self.all_item_attr:
            attr = wx.ListItemAttr()
            attr.SetTextColour( colour )
            self.all_item_attr[ colour ] = attr

        return self.all_item_attr[ colour ]

    # ----------------------------------------
    def initButtons( self, sizer ):
        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        #self.button_view = wx.Button( self.panel_history, id_view_cmd, " View " )
        #self.button_view.Enable( False )

        self.button_diff = wx.Button( self.panel_history, id_diff_cmd, T_('Diff') )
        self.button_diff.Enable( False )
        self.button_annotate = wx.Button( self.panel_history, id_annotate_cmd, T_('Annotate') )
        self.button_annotate.Enable( False )
        self.button_revision_changes = wx.Button( self.panel_history, id_revision_changes_cmd, T_('Revision Changes') )
        self.button_revision_changes.Enable( False )

        # leave View off screen until its implemented
        #self.h_sizer.Add( self.button_view, 0, wx.EXPAND|wx.LEFT, 5 )
        self.h_sizer.Add( self.button_diff, 0, wx.EXPAND|wx.LEFT, 5 )
        self.h_sizer.Add( self.button_annotate, 0, wx.EXPAND|wx.LEFT, 5 )
        self.h_sizer.Add( self.button_revision_changes, 0, wx.EXPAND|wx.LEFT, 5 )

        sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_BUTTON( self.panel_history, id_view_cmd, self.OnViewCommand )
        wx.EVT_BUTTON( self.panel_history, id_diff_cmd, self.OnDiffCommand )
        wx.EVT_BUTTON( self.panel_history, id_annotate_cmd, self.OnAnnotateCommand )
        wx.EVT_BUTTON( self.panel_history, id_revision_changes_cmd, self.OnRevisionChangesCommand )

        wx.EVT_UPDATE_UI( self.panel_history, id_diff_cmd, self.OnUpdateUiDiffCommand )
        wx.EVT_UPDATE_UI( self.panel_history, id_annotate_cmd, self.OnUpdateUiAnnotateCommand )
        wx.EVT_UPDATE_UI( self.panel_history, id_revision_changes_cmd, self.OnUpdateUiRevisionChangesCommand )

    def getSelectedRows( self ):
        all_rows = []
        item_index = -1
        while True:
            item_index = self.list_ctrl.GetNextItem( item_index, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED )
            if item_index < 0:
                break

            all_rows.append( item_index )

        return all_rows

    #---------- Event handlers ----------------------------------------------------------
    def OnListItemSelected( self, event):
        self.updateComment( event.m_itemIndex )

    def OnListItemDeselected( self, event):
        self.updateComment( -1 )

    def OnPathItemSelected( self, event):
        pass

    def OnPathItemDeselected( self, event):
        pass

    #---------- Comment handlers ------------------------------------------------------------
    def updateComment( self, index ):
        if index >= 0:
            message = self.all_filtered_log_entries[ index ].message
            all_paths_info = self.all_filtered_log_entries[ index ].changed_paths
        else:
            message = ''
            all_paths_info = []

        self.comment_ctrl.SetValue( message )
        self.comment_ctrl.SetInsertionPoint( 0 )

        self.paths_ctrl.DeleteAllItems()
        for index, info in enumerate( all_paths_info ):
            self.paths_ctrl.InsertStringItem( index,
                action_map.get( info.action, info.action ) )
            self.paths_ctrl.SetStringItem( index, self.col_path,
                info.path )
            if info.copyfrom_path is not None:
                self.paths_ctrl.SetStringItem( index, self.col_copyfrom_revision,
                    str( info.copyfrom_revision.number ) )
                self.paths_ctrl.SetStringItem( index, self.col_copyfrom_path,
                    info.copyfrom_path )
            else:
                self.paths_ctrl.SetStringItem( index, self.col_copyfrom_revision, '' )
                self.paths_ctrl.SetStringItem( index, self.col_copyfrom_path, '' )

    def OnSizeHistory( self, event):
        w,h = self.panel_history.GetClientSizeTuple()
        self.v_sizer_history.SetDimension( 0, 0, w, h )

    def OnSizeComment( self, event):
        w,h = self.panel_comment.GetClientSizeTuple()
        self.v_sizer_comment.SetDimension( 0, 0, w, h )

    def OnSizeChangedPaths( self, event):
        w,h = self.panel_changed_paths.GetClientSizeTuple()
        self.v_sizer_changed_paths.SetDimension( 0, 0, w, h )

    def by_rev( self, a, b ):
        # highest rev first
        return -cmp( a.rev_number, b.rev_number )

    def initList( self ):
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.SetItemCount( len(self.all_filtered_log_entries) )
        if len(self.all_filtered_log_entries) > 0:
            self.list_ctrl.RefreshItems( 0, len(self.all_filtered_log_entries)-1 )
            self.list_ctrl.SetItemState( 0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED )

    #---------- Command handlers ----------------------------------------------------------
    def OnViewCommand( self, event ):
        print T_('Log history View not implemented')

    def OnUpdateUiDiffCommand( self, event ):
        all_rows = self.getSelectedRows()
        self.button_diff.Enable( len( all_rows ) in (1,2) )

    def OnDiffCommand( self, event ):
        indices = self.getSelectedRows()

        indices.sort()
        indices.reverse()

        if len( indices ) not in (1,2):
            return

        info1 = wb_subversion_diff.PathInfoForDiff()

        info1.path = self.all_filtered_log_entries[ indices[0] ].url
        info1.revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                self.all_filtered_log_entries[ indices[0] ].rev_number )
        info1.peg_path = self.all_filtered_log_entries[ 0 ].url
        info1.peg_revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                self.all_filtered_log_entries[ 0 ].rev_number )
        info1.title = '%s@%d' % (info1.path, info1.revision.number)

        info2 = info1.copy()

        if len( indices ) == 1:
            info2.path = self.filename
            info2.revision = pysvn.Revision( pysvn.opt_revision_kind.working )
            info2.peg_path = info2.path
            info2.peg_revision = info2.revision
            info2.title = self.filename
        else:
            info2.path = self.all_filtered_log_entries[ indices[1] ].url
            info2.revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                self.all_filtered_log_entries[ indices[1] ].rev_number )
            info2.title = '%s@%d' % (info2.path, info2.revision.number)

        generator = self.parent.diffFunction(
                    self.app,
                    self.project_info,
                    info1, info2 )

        #
        #   history does not need to have the diff code run in the background
        #   so just step the generator
        #
        if type(generator) == types.GeneratorType:
            while True:
                try:
                    generator.next()
                except StopIteration:
                    # no problem all done
                    break

    def OnUpdateUiAnnotateCommand( self, event ):
        all_rows = self.getSelectedRows()
        self.button_annotate.Enable( len( all_rows ) in (1,2) )

    def OnAnnotateCommand( self, event ):
        indices = self.getSelectedRows()

        indices.sort()

        if len( indices ) not in (1,2):
            return

        if len( indices ) == 2:
            rev_start = pysvn.Revision( pysvn.opt_revision_kind.number,
                                    self.all_filtered_log_entries[ indices[1] ].rev_number )
            rev_end = pysvn.Revision( pysvn.opt_revision_kind.number,
                                    self.all_filtered_log_entries[ indices[0] ].rev_number )

        elif len( indices ) == 1:
            rev_start = pysvn.Revision( pysvn.opt_revision_kind.number, 0 )
            rev_end = pysvn.Revision( pysvn.opt_revision_kind.number,
                                    self.all_filtered_log_entries[ indices[0] ].rev_number )

        try:
            annotation = self.project_info.client_fg.annotate(
                            url_or_path=self.filename,
                            revision_start=rev_start,
                            revision_end=rev_end,
                            peg_revision=rev_end )

        except pysvn.ClientError, e:
            self.app.log_client_error( e )
            return

        h_frame = wb_subversion_annotate.AnnotateFrame( self.app, self.project_info, self.filename, annotation )
        h_frame.Show( True )



    def OnUpdateUiRevisionChangesCommand( self, event ):
        self.button_revision_changes.Enable( len( self.getSelectedRows() ) in (1, 2) )

    def OnRevisionChangesCommand( self, event ):
        row_indices = self.getSelectedRows()

        info1 = wb_subversion_diff.PathInfoForDiff()
        info1.path = self.all_filtered_log_entries[ row_indices[0] ].url
        info2 = info1.copy()
        if len( row_indices ) == 1:
            # for one selected revision N, show files modified in revision N
            # and set the diff range to N-1..N.
            log_entries = [self.all_filtered_log_entries[ row_indices[0] ]]
            info1.revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                             self.all_filtered_log_entries[ row_indices[0] ].rev_number-1 )
        else:
            # for two selected revisions N and M, show files modified in revisions N+1..M
            # and set the diff range to N..M.
            # note that all_filtered_log_entries contains lower revisions at higher indices.
            log_entries = self.all_filtered_log_entries[ row_indices[0]:row_indices[1] ]
            info1.revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                             self.all_filtered_log_entries[ row_indices[1] ].rev_number )
        info2.revision = pysvn.Revision( pysvn.opt_revision_kind.number,
                                         self.all_filtered_log_entries[ row_indices[0] ].rev_number )
        info1.peg_revision = info1.revision
        info2.peg_revision = info2.revision

        changed_states = {}

        repos_root_url = self.project_info.client_bg.info2( self.project_info.wc_path, recurse=False )[0][1].repos_root_URL
        prefix_len = len( self.all_filtered_log_entries[row_indices[0]].url ) - len( repos_root_url )
        for log_entry in log_entries:
            if log_entry.url == self.all_filtered_log_entries[row_indices[0]].url:
                for changed_path in log_entry.changed_paths:
                    repository_path = changed_path['path']
                    url = repos_root_url + repository_path

                    if changed_states.has_key(repository_path):
                        branch_text_states = changed_states[repository_path]['branch_text_states']
                    else:
                        branch_text_states = ''
                    branch_text_states += changed_path['action']

                    # Create a new status object from the log entry data.
                    entry = pysvn.PysvnEntry(
                                {'checksum': ''
                                ,'commit_author': log_entry.author
                                ,'commit_revision': log_entry.rev_number
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
                                ,'revision': log_entry.rev_number
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
                                ,'path': repository_path
                                ,'prop_status': pysvn.wc_status_kind.normal
                                ,'repos_lock': None
                                ,'repos_prop_status': pysvn.wc_status_kind.none
                                ,'repos_text_status': pysvn.wc_status_kind.none
                                ,'branch_text_states': branch_text_states
                                ,'text_status': pysvn.wc_status_kind.normal})
                    changed_states[repository_path] = status
            else:
               self.app.log.info( T_('Revision changes for r%(rev1)d ignored. Its URL "%(url1)s" does not match r%(rev2)d URL "%(url2)s".') %
                                    {'rev1': log_entry.rev_number
                                    ,'url1': log_entry.url
                                    ,'rev2': self.all_filtered_log_entries[row_indices[0]].rev_number
                                    ,'url2': self.all_filtered_log_entries[row_indices[0]].url} )

        changed_files = [changed_states[status] for status in changed_states]

        self.app.showReportRevisionChangesFrame( self.project_info, changed_files, info1, info2 )
