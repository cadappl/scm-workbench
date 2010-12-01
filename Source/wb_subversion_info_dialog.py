'''
 ====================================================================
 Copyright (c) 2003-2007 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_list_handler.py

'''
import types
import pysvn
import wx
import wb_subversion_utils

class InfoDialog(wx.Dialog):
    def __init__( self, app, parent, path, info_entry_or_info2_list ):
        wx.Dialog.__init__( self, parent, -1, path )

        self.g_sizer = None
        self.g_sizer_list = []

        self.addGroup( T_('Entry') )
        value_ctrl = self.addRow( T_('Path:') ,path )
        value_ctrl.SetFocus()

        #print 'info_entry_or_info2_list',info_entry_or_info2_list
        if type(info_entry_or_info2_list) == types.ListType:
            self.initForInfo2( info_entry_or_info2_list[0][1] )
        else:
            self.initForInfo1( info_entry_or_info2_list )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (450, 20), 1, wx.EXPAND)
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        for g_sizer in self.g_sizer_list:
            self.v_sizer.Add( g_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

    def initForInfo1( self, entry ):
        if entry.name and entry.name != 'svn:this_dir':
            self.addRow( T_('Name:'), entry.name )
        if entry.url:
            self.addRow( T_('URL:'), entry.url )
        if entry.repos:
            self.addRow( T_('Repository:'), entry.repos )
        if entry.uuid:
            self.addRow( T_('Repository UUID:'), entry.uuid )
        if entry.revision.kind == pysvn.opt_revision_kind.number:
            self.addRow( T_('Revision:'), entry.revision.number )
        if entry.kind == pysvn.node_kind.file:
            self.addRow( T_('Node kind:'), T_('file') )
        elif entry.kind == pysvn.node_kind.dir:
            self.addRow( T_('Node kind:'), T_('directory') )
        elif entry.kind == pysvn.node_kind.none:
            self.addRow( T_('Node kind:'), T_('none') )
        else:
            self.addRow( T_('Node kind:'), T_('unknown') )

        if entry.schedule == pysvn.wc_schedule.normal:
            self.addRow( T_('Schedule:'), T_('normal') )
        elif entry.schedule == pysvn.wc_schedule.add:
            self.addRow( T_('Schedule:'), T_('add') )
        elif entry.schedule == pysvn.wc_schedule.delete:
            self.addRow( T_('Schedule:'), T_('delete') )
        elif entry.schedule == pysvn.wc_schedule.replace:
            self.addRow( T_('Schedule:'), T_('replace') )
        if entry.is_copied:
            if entry.copy_from_url:
                self.addRow( T_('Copied From URL:'), entry.copy_from_url )
            if entry.copy_from_rev.number:
                self.addRow( T_('Copied From Revision:'), entry.copy_from_rev.number )
        if entry.commit_author:
            self.addRow( T_('Last Changed Author:'), entry.commit_author )
        if entry.commit_revision.number > 0:
            self.addRow( T_('Last Changed Revision:'), entry.commit_revision.number )
        if entry.commit_time:
            self.addRow( T_('Last Changed Date:'), wb_subversion_utils.fmtDateTime( entry.commit_time ) )
        if entry.text_time:
            self.addRow( T_('Text Last Updated:'), wb_subversion_utils.fmtDateTime( entry.text_time ) )
        if entry.properties_time:
            self.addRow( T_('Properties Last Updated:'), wb_subversion_utils.fmtDateTime( entry.properties_time ) )
        if entry.checksum:
            self.addRow( T_('Checksum:'), entry.checksum )

    def initForInfo2( self, entry ):
        if entry['URL']:
            self.addRow( T_('URL:'), entry['URL'] )
        if entry['repos_root_URL']:
            self.addRow( T_('Repository root URL:'), entry['repos_root_URL'] )
        if entry['repos_UUID']:
            self.addRow( T_('Repository UUID:'), entry['repos_UUID'] )
        if entry['rev'].kind == pysvn.opt_revision_kind.number:
            self.addRow( T_('Revision:'), entry['rev'].number )
        if entry['kind'] == pysvn.node_kind.file:
            self.addRow( T_('Node kind:'), T_('file') )
        elif entry['kind'] == pysvn.node_kind.dir:
            self.addRow( T_('Node kind:'), T_('directory') )
        elif entry['kind'] == pysvn.node_kind.none:
            self.addRow( T_('Node kind:'), T_('none') )
        else:
            self.addRow( T_('Node kind:'), T_('unknown') )

        if entry['last_changed_author']:
            self.addRow( T_('Last Changed Author:'), entry['last_changed_author'] )
        if entry['last_changed_rev'].number > 0:
            self.addRow( T_('Last Changed Revision:'), entry['last_changed_rev'].number )
        if entry['last_changed_date']:
            self.addRow( T_('Last Changed Date:'), wb_subversion_utils.fmtDateTime( entry['last_changed_date'] ) )

        self.addGroup( T_('Lock') )
        lock_info = entry['lock']
        if lock_info is not None:
            self.addRow( T_('Lock Owner:'), lock_info['owner'] )
            self.addRow( T_('Lock Creation Date:'), wb_subversion_utils.fmtDateTime( lock_info['creation_date'] ) )
            if lock_info['expiration_date'] is not None:
                self.addRow( T_('Lock Expiration Date:'), wb_subversion_utils.fmtDateTime( lock_info['expiration_date'] ) )
            self.addRow( T_('Lock Token:'), lock_info['token'] )
            self.addRow( T_('Lock Comment:'), lock_info['comment'] )
        else:
            self.addRow( T_('Lock Token:'), '' )

        wc_info = entry['wc_info']
        if wc_info is None:
            return

        self.addGroup( T_('Working copy') )
        if wc_info['schedule'] == pysvn.wc_schedule.normal:
            self.addRow( T_('Schedule:'), T_('normal') )
        elif wc_info['schedule'] == pysvn.wc_schedule.add:
            self.addRow( T_('Schedule:'), T_('add') )
        elif wc_info['schedule'] == pysvn.wc_schedule.delete:
            self.addRow( T_('Schedule:'), T_('delete') )
        elif wc_info['schedule'] == pysvn.wc_schedule.replace:
            self.addRow( T_('Schedule:'), T_('replace') )
        else:
            self.addRow( T_('Schedule:'), unicode(wc_info['schedule']))
        if wc_info['copyfrom_url']:
            self.addRow( T_('Copied From URL:'), wc_info['copyfrom_url'] )
            if wc_info['copyfrom_rev'].number:
                self.addRow( T_('Copied From Revision:'), wc_info['copyfrom_rev'].number )
        if wc_info['text_time']:
            self.addRow( T_('Text Last Updated:'), wb_subversion_utils.fmtDateTime( wc_info['text_time'] ) )
        if wc_info['prop_time']:
            self.addRow( T_('Properties Last Updated:'), wb_subversion_utils.fmtDateTime( wc_info['prop_time'] ) )
        if wc_info['checksum']:
            self.addRow( T_('Checksum:'), wc_info['checksum'] )

    def addGroup( self, label ):
        self.g_sizer = wx.FlexGridSizer( 0, 2, 5, 5 )
        self.g_sizer.AddGrowableCol( 1 )

        self.border = wx.StaticBox( self, -1, label )
        self.box = wx.StaticBoxSizer( self.border, wx.VERTICAL )
        self.box.Add( self.g_sizer, 0, wx.EXPAND )

        self.g_sizer_list.append( self.box )

    def addRow( self, label, value ):
        label_ctrl = wx.StaticText( self, -1, label, style=wx.ALIGN_RIGHT )
        str_value = unicode(value)

        # cannot set the controls readonly as that prevent copy of the text
        if '\n' in str_value:
            value_ctrl = wx.TextCtrl( self, -1, unicode(value), size=wx.Size( -1, 100 ),
                                        style=wx.TE_MULTILINE )
        else:
            value_ctrl = wx.TextCtrl( self, -1, unicode(value) )
        # value_ctrl.SetSelection( -1, -1 )

        self.g_sizer.Add( label_ctrl, 1, wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 3 )
        self.g_sizer.Add( value_ctrl, 0, wx.EXPAND|wx.RIGHT, 3)
        return value_ctrl
