'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_dialogs.py

'''
import wx
import re
import os

id_log_message_text = wx.NewId()
id_last_log_message = wx.NewId()

class DialogBuildingBlock(wx.Dialog):
    def __init__( self, parent, title ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.title = title
        self.all_filenames = []

        self.add_filename_list_field = False
        self.add_log_message_field = False
        self.add_force_field = False

    def initControls( self ):
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.filename_list = None
        if self.add_filename_list_field:
            self.filename_list = wx.ListCtrl( self, -1, wx.DefaultPosition, wx.Size( 600, 200 ), wx.LC_REPORT|wx.NO_BORDER )
            self.filename_list.InsertColumn( 0, T_("Status") )
            self.filename_list.SetColumnWidth( 0, 50 )
            self.filename_list.InsertColumn( 1, T_("Filename") )
            self.filename_list.SetColumnWidth( 1, 1000 )

            for index, _ in enumerate( self.all_filenames ):
                self.filename_list.InsertStringItem( index, self.all_filenames[index][0] )
                self.filename_list.SetStringItem( index, 1, self.all_filenames[index][1] )

        self.log_message_ctrl = None
        if self.add_log_message_field:
            self.log_message_ctrl = wx.TextCtrl( self, id_log_message_text, size=wx.Size( 600, 200 ), style=wx.TE_MULTILINE )
            self.log_message_ctrl.SetFocus()

        self.force_checkbox_ctrl = None
        if self.add_force_field:
            self.force_checkbox_ctrl = wx.CheckBox( self, -1, T_("Force") )
            self.force_checkbox_ctrl.SetValue( False )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(" OK ") )
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(" Cancel ") )
        self.button_ok.SetDefault()

        self.initExtraButtons()

        self.h_sizer.Add( (60, 20), 1, wx.EXPAND)
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15)
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        if self.add_filename_list_field:
            self.v_sizer.Add( self.filename_list, 0, wx.EXPAND|wx.ALL, 5 )
        if self.add_log_message_field:
            self.v_sizer.Add( self.log_message_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
        if self.add_force_field:
            self.v_sizer.Add( self.force_checkbox_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def initExtraButtons( self ):
        pass

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getLogMessage( self ):
        return self.log_message_ctrl.GetValue()

    def getForce( self ):
        return self.force_checkbox_ctrl.GetValue() != 0

class ConfirmAction(DialogBuildingBlock):
    def __init__( self, parent, title, all_filenames, force_field=False ):
        DialogBuildingBlock.__init__( self, parent, title )

        self.all_filenames = all_filenames
        self.add_filename_list_field = True
        self.add_force_field = force_field

        self.initControls()

class LogMessage(DialogBuildingBlock):
    def __init__( self, parent, title, all_filenames, message_filename=None, force_field=False ):
        DialogBuildingBlock.__init__( self, parent, title )
        self.all_filenames = all_filenames

        self.add_filename_list_field = True
        self.add_log_message_field = True
        self.add_force_field = force_field

        self.message_filename = message_filename
        self.last_log_message_text = None
        if self.message_filename is not None:
            try:
                self.last_log_message_text = file( self.message_filename, 'r' ).read().decode('utf-8').strip()
            except EnvironmentError:
                self.last_log_message_text = ''

        self.initControls()

    def initExtraButtons( self ):
        if self.last_log_message_text is not None:
            self.button_last_log_message = wx.Button( self, id_last_log_message, T_("Insert Last Message") )
            self.button_last_log_message.Enable( len(self.last_log_message_text) > 0 )
            self.h_sizer.Add( self.button_last_log_message )

        self.button_ok.Enable( False )

        wx.EVT_BUTTON( self, id_last_log_message, self.OnInsertLastLogMessage )
        wx.EVT_TEXT( self, id_log_message_text, self.OnLogMessageChanged )

    def OnInsertLastLogMessage( self, event ):
        self.log_message_ctrl.WriteText( self.last_log_message_text )
        self.button_ok.Enable( True )

    def OnLogMessageChanged( self, event ):
        self.button_ok.Enable( len( self.log_message_ctrl.GetValue().strip() ) > 0 )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )
        try:
            file( self.message_filename, 'w' ).write( self.getLogMessage().encode('utf-8') )
        except (IOError,OSError):
            pass

class GetCredentials(wx.Dialog):
    def __init__( self, parent, title, username, may_save ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.border = wx.StaticBox( self, -1, T_('Credentials') )
        self.box = wx.StaticBoxSizer( self.border, wx.VERTICAL )
        self.box.Add( self.g_sizer, 0, wx.EXPAND )

        self.username_label = wx.StaticText( self, -1, T_('Username:') )
        self.username_ctrl = wx.TextCtrl( self, -1, username )
        self.username_ctrl.SetFocus()
        self.username_ctrl.SetSelection( -1, -1 )

        self.g_sizer.Add( self.username_label, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.username_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        self.password_label = wx.StaticText(self, -1, T_('Password:') )
        self.password_ctrl = wx.TextCtrl(self, -1, '', style=wx.TE_PASSWORD )

        self.g_sizer.Add( self.password_label, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.password_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        self.save_ctrl = wx.CheckBox( self, -1, T_("Always uses these credentials") )
        self.save_ctrl.SetValue( may_save )
        self.g_sizer.Add( self.save_ctrl, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( (1, 1) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (250, 20), 1, wx.EXPAND)
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getUsername( self ):
        return self.username_ctrl.GetValue()

    def getPassword( self ):
        return self.password_ctrl.GetValue()

    def getSaveCredentials( self ):
        return self.save_ctrl.GetValue() != 0

class GetServerTrust(wx.Dialog):
    def __init__( self, parent, realm, info_list, may_save ):
        wx.Dialog.__init__( self, parent, -1, T_('Trust server %s') % realm )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.border = wx.StaticBox( self, -1, T_('Server Certificate') )
        self.box = wx.StaticBoxSizer( self.border, wx.VERTICAL )
        self.box.Add( self.g_sizer, 0, wx.EXPAND )

        for key, value in info_list:
            self.addRow( key, value )

        self.save_ctrl = wx.CheckBox( self, -1, T_("Always trust this server") )
        self.save_ctrl.SetValue( may_save )
        self.g_sizer.Add( self.save_ctrl, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( (1, 1) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (250, 20), 1, wx.EXPAND)
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def addRow( self, label, value ):
        label_ctrl = wx.StaticText( self, -1, label, style=wx.ALIGN_RIGHT )
        value_ctrl = wx.TextCtrl( self, -1, str(value), style=wx.TE_READONLY )

        self.g_sizer.Add( label_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( value_ctrl, 0, wx.EXPAND, 5 )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getSaveTrust( self ):
        return self.save_ctrl.GetValue() != 0

class AddDialog(wx.Dialog):
    def __init__( self, parent, title, filename, force=False, recursive=None ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.add_border = wx.StaticBox( self, -1, T_('Add') )
        self.add_box = wx.StaticBoxSizer( self.add_border, wx.VERTICAL )
        self.add_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.filename_text = wx.StaticText( self, -1, T_('From:') )
        self.filename_ctrl = wx.StaticText( self, -1, filename )

        self.g_sizer.Add( self.filename_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.filename_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        self.force_ctrl = wx.CheckBox( self, -1, T_('Force Add') )
        self.force_ctrl.SetValue( force )
        self.g_sizer.Add( self.force_ctrl, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( (1, 1) )

        if recursive is not None:
            self.recursive_ctrl = wx.CheckBox( self, -1, T_('Recursive Add') )
            self.recursive_ctrl.SetValue( recursive )
            self.g_sizer.Add( self.recursive_ctrl, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
            self.g_sizer.Add( (1, 1) )

        else:
            self.recursive_ctrl = None

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.add_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getForce( self ):
        if self.force_ctrl is None:
            return False

        return self.force_ctrl.GetValue() != 0

    def getRecursive( self ):
        if self.recursive_ctrl is None:
            return False

        return self.recursive_ctrl.GetValue() != 0

class RenameFile(wx.Dialog):
    def __init__( self, parent, title, old_filename, force=None ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.rename_border = wx.StaticBox( self, -1, T_('Rename') )
        self.rename_box = wx.StaticBoxSizer( self.rename_border, wx.VERTICAL )
        self.rename_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.old_filename_text = wx.StaticText( self, -1, T_('From:') )
        self.old_filename_ctrl = wx.StaticText( self, -1, old_filename )

        self.g_sizer.Add( self.old_filename_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.old_filename_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        self.new_filename_text = wx.StaticText( self, -1, T_('To:') )
        self.new_filename_ctrl = wx.TextCtrl( self, -1, old_filename )
        self.new_filename_ctrl.SetSelection( -1, -1 )
        self.new_filename_ctrl.SetFocus()

        self.g_sizer.Add( self.new_filename_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.new_filename_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        if force is None:
            self.force_ctrl = None
        else:
            self.force_ctrl = wx.CheckBox( self, -1, T_("Force rename") )
            self.force_ctrl.SetValue( force )
            self.g_sizer.Add( self.force_ctrl, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
            self.g_sizer.Add( (1, 1) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.rename_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getNewFilename( self ):
        return self.new_filename_ctrl.GetValue()

    def getForce( self ):
        if self.force_ctrl is None:
            return False
        return self.force_ctrl.GetValue() != 0

class GetFilename(wx.Dialog):
    def __init__( self, parent, title, border_title ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.rename_border = wx.StaticBox( self, -1, border_title )
        self.rename_box = wx.StaticBoxSizer( self.rename_border, wx.VERTICAL )
        self.rename_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.new_filename_text = wx.StaticText( self, -1, T_('Name:') )
        self.new_filename_ctrl = wx.TextCtrl( self, -1, T_('New Folder') )
        self.new_filename_ctrl.SetSelection( -1, -1 )
        self.new_filename_ctrl.SetFocus()

        self.g_sizer.Add( self.new_filename_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.new_filename_ctrl, 0, wx.EXPAND|wx.EAST, 5 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.rename_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getNewFilename( self ):
        return self.new_filename_ctrl.GetValue()

class NewFile(wx.Dialog):
    template_suffix = '.template'

    def __init__( self, parent, template_dir ):
        wx.Dialog.__init__( self, parent, -1, T_('New File') )

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.newfile_border = wx.StaticBox( self, -1, T_('New File') )
        self.newfile_box = wx.StaticBoxSizer( self.newfile_border, wx.VERTICAL )
        self.newfile_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.newfile_text = wx.StaticText( self, -1, T_('New Filename:') )
        self.newfile_ctrl = wx.TextCtrl( self, -1, '' )
        self.newfile_ctrl.SetFocus()
        self.newfile_ctrl.SetSelection( -1, -1 )

        self.g_sizer.Add( self.newfile_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.newfile_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        try:
            self.template_file_list = [filename[:-len(self.template_suffix)]
                                        for filename in os.listdir( template_dir )
                                            if filename.lower().endswith( self.template_suffix )]
        except EnvironmentError:
            self.template_file_list = []

        self.template_text = wx.StaticText( self, -1, T_('Template:') )
        self.template_list = wx.Choice( self, -1, choices=self.template_file_list )
        self.template_list.SetSelection( 0 )

        self.g_sizer.Add( self.template_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.template_list, 0, wx.EXPAND|wx.ALL, 5 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.newfile_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getNewFilename( self ):
        return self.newfile_ctrl.GetValue()

    def getTemplateFilename( self ):
        index = self.template_list.GetCurrentSelection()
        if index >= 0 and len(self.template_file_list) > index:
            return self.template_file_list[ index ] + self.template_suffix
        else:
            return None


class CopyUrl(wx.Dialog):
    def __init__( self, parent, app, title, copy_from_url, copy_to_url ):
        wx.Dialog.__init__( self, parent, -1, '%s %s' % (title, copy_from_url) )

        self.app = app
        self.copy_to_url = copy_to_url
        p = self.app.prefs.getAdvanced()
        self.arbitrary_path = p.arbitrary_tag_branch
        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.copyurl_border = wx.StaticBox( self, -1, title )
        self.copyurl_box = wx.StaticBoxSizer( self.copyurl_border, wx.VERTICAL )
        self.copyurl_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.copy_from_label = wx.StaticText( self, -1, T_('Copy From:') )
        self.copy_from_value = wx.StaticText( self, -1, copy_from_url )

        self.copy_to_label = wx.StaticText( self, -1, T_('Copy To:') )
        if not self.arbitrary_path:
            self.copy_to_root = wx.StaticText( self, -1, copy_to_url + '/' )
            self.copy_to_leaf = wx.TextCtrl( self, -1, '', size=(300, -1) )
        else:
            # should place repos_root_URL as a static prefix
            self.copy_to_browse = wx.StaticText( self, -1, '' )
            self.copy_to_leaf = wx.TextCtrl( self, -1, copy_to_url + '/', size=(500, -1) )

        self.copy_to_leaf.SetFocus()

        self.h_sizer_copy_to = wx.BoxSizer( wx.HORIZONTAL )
        if not self.arbitrary_path:
            self.h_sizer_copy_to.Add( self.copy_to_root, 0, wx.EXPAND|wx.EAST, 15 )
            self.h_sizer_copy_to.Add( self.copy_to_leaf, 0, wx.EXPAND|wx.EAST, 2 )
        else:
            self.h_sizer_copy_to.Add( self.copy_to_leaf, 1, wx.EXPAND|wx.EAST, 2 )
            self.h_sizer_copy_to.Add( self.copy_to_browse, 0, wx.EXPAND|wx.EAST, 2 )

        self.g_sizer.Add( self.copy_from_label, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.copy_from_value, 0, wx.EXPAND|wx.ALL, 5 )

        self.g_sizer.Add( self.copy_to_label, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.h_sizer_copy_to, 0, wx.EXPAND|wx.ALL, 5 )

        self.label_ctrl = wx.StaticText( self, -1, T_('Log message'), style=wx.ALIGN_LEFT )
        self.log_message_ctrl = wx.TextCtrl( self, -1, style=wx.TE_MULTILINE )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_ok.Enable( False )
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.copyurl_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.label_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.log_message_ctrl, 1, wx.EXPAND|wx.ALL, 5 )

        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_TEXT( self, self.log_message_ctrl.GetId(), self.OnLogMessageChanged )
        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

        self.copy_to_label.SetFocus()

    def OnLogMessageChanged( self, event ):
        self.button_ok.Enable(
                len( self.log_message_ctrl.GetValue().strip() ) > 0
            and len( self.copy_to_leaf.GetValue().strip() ) > 0 )

    def OnOk( self, event ):
        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def getCopyTo( self ):
        if not self.arbitrary_path:
            return '%s/%s' % (self.copy_to_url, self.copy_to_leaf.GetValue().strip())
        else:
            return self.copy_to_leaf.GetValue().strip()

    def getCopyToLeaf( self ):
        return self.copy_to_leaf.GetValue().strip()

    def getLogMessage( self ):
        return self.log_message_ctrl.GetValue()

class CreateTag(CopyUrl):
    def __init__( self, parent, app, copy_from_url, copy_to_url ):
        CopyUrl.__init__( self, parent, app, T_('Create Tag'), copy_from_url, copy_to_url )

class CreateBranch(CopyUrl):
    def __init__( self, parent, app, copy_from_url, copy_to_url ):
        CopyUrl.__init__( self, parent, app, T_('Create Branch'), copy_from_url, copy_to_url )

class NewIdent(wx.Dialog):
    def __init__( self, parent, title, dir_name, ban_list, no_name ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.dir_name = dir_name
        self.ban_list = ban_list

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.newfile_border = wx.StaticBox( self, -1, T_('New Ident') )
        self.newfile_box = wx.StaticBoxSizer( self.newfile_border, wx.VERTICAL )
        self.newfile_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.newfile_text = wx.StaticText( self, -1, T_('Ident Name:') )
        self.newfile_ctrl = wx.TextCtrl( self, -1, '' )
        if no_name:
            self.newfile_ctrl.SetValue( self.dir_name )
            self.newfile_ctrl.Enable( False )

        self.newfile_ctrl.SetFocus()
        self.newfile_ctrl.SetSelection( -1, -1 )

        self.g_sizer.Add( self.newfile_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.newfile_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.tag_text = wx.StaticText( self, -1, T_('New Label:') )
        # calculate a new one
        suggested_label = self.calculateNewLabel( self.dir_name, ban_list )
        self.tag_ctrl = wx.TextCtrl( self, -1, suggested_label )

        self.g_sizer.Add( self.tag_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.tag_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()

        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.newfile_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )
        wx.EVT_TEXT( self, self.tag_ctrl.GetId(), self.OnTagCtrlChange )

        self.OnTagCtrlChange( None )

    def OnOk( self, event ):
        prefix  = '%s-' % self.dir_name.upper()

        if len( self.newfile_ctrl.GetValue().strip() ) == 0:
            wx.MessageBox( T_('The label is existent, please use a new one'),
                           style=wx.OK|wx.ICON_ERROR )

        if self.tag_ctrl.GetValue() in self.ban_list:
            wx.MessageBox( T_('The label is existent, please use a new one'),
                           style=wx.OK|wx.ICON_ERROR )
            return

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def OnTagCtrlChange( self, event ):
        prefix  = '%s-' % self.dir_name.upper()
        tag_str = self.tag_ctrl.GetValue().strip()

        if len( tag_str ) > len( prefix ):
            self.button_ok.Enable( tag_str.startswith( prefix ) )

    def getDirName( self ):
        return self.newfile_ctrl.GetValue().strip()

    def getTagName( self ):
        return self.tag_ctrl.GetValue().strip()

    def calculateNewLabel( self, dir_name, tags ):
        major, minor, subver = ( -1, -1, -1 )
        for tag in tags:
            m = re.match( '[^-]+-[^\d]*(\d+)\.(\d+)\.(\d+)', tag )
            if m:
                a, b, c = ( int( m.group(1) ), int( m.group(2) ), int( m.group(3) ) )
            else:
                m = re.match( '[^-]+-[^\d]*(\d+)\.(\d+)', tag )
                if m:
                    a, b, c = ( int( m.group(1) ), int( m.group(2) ), -1 )

            if a > major:
                major, minor, subver = ( a, -1, -1 )
            if b > minor:
                minor, subver = ( b, -1 )
            if c > subver:
                subver = c

        uname = dir_name.upper()
        if major == -1:
            major = 1

        if subver == -1:
            return '%s-%d.%d' % ( uname, major, minor + 1 )
        else:
            return '%s-%d.%d.%d' % ( uname, major, minor, subver + 1 )
