'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_properties_dialog.py

'''
import os
import time
import fnmatch
import pysvn
import threading
import wx
import wb_source_control_providers
import wb_subversion_history
import wb_subversion_annotate
import wb_tree_panel
import wb_list_panel
import wb_ids
import wb_exceptions

class SingleProperty:
    id_map = {}
    def __init__( self, dialog, name, present ):
        self.dialog = dialog
        self.name = name
        self.was_present = present
        self.starting_value = ''
        self.value_ctrl = None

        if not SingleProperty.id_map.has_key( name ):
            SingleProperty.id_map[ name ] = (wx.NewId(), wx.NewId())

        self.ctrl_id, self.value_id = SingleProperty.id_map[ name ]

        self.checkbox = wx.CheckBox( dialog, self.ctrl_id, name )
        self.checkbox.SetValue( present )

        wx.EVT_CHECKBOX( self.dialog, self.ctrl_id, self.OnCheckBox )

        self.dialog.g_sizer.Add( self.checkbox, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

    def setValueCtrl( self, value_ctrl, value ):
        self.starting_value = value
        self.value_ctrl = value_ctrl

        self.value_ctrl.Enable( self.was_present )

        self.dialog.g_sizer.Add( self.value_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

    def OnCheckBox( self, event ):
        self.value_ctrl.Enable( self.checkbox.IsChecked() )

    def isValid( self ):
        return True

    def isModified( self ):
        if self.was_present ^ self.isPresent():
            return True

        return self.checkbox.IsChecked() and self.starting_value != self.getValue()

    def isPresent( self ):
        if self.checkbox.IsChecked():
            return True
        else:
            return False

    def getName( self ):
        return self.name

    def getValue( self ):
        return ''

class SinglePropertyText(SingleProperty):
    def __init__( self, dialog, name, present, value ):
        SingleProperty.__init__( self, dialog, name, present )

        self.setValueCtrl( wx.TextCtrl( self.dialog, self.value_id, value, size=(300,-1) ), value )

    def isValid( self ):
        if not self.isPresent():
            return True

        text = self.value_ctrl.GetValue()
        if text.strip() == '':
            wx.MessageBox( T_('Enter a value for %s') % self.name,
                T_('Warning'), style=wx.OK|wx.ICON_EXCLAMATION )
            return False
        return True

    def getValue( self ):
        return self.value_ctrl.GetValue()

class SinglePropertyMultiLine(SingleProperty):
    def __init__( self, dialog, name, present, value ):
        SingleProperty.__init__( self, dialog, name, present )

        self.setValueCtrl( wx.TextCtrl( self.dialog, self.value_id, value,
                                size=(600,100), style=wx.TE_MULTILINE|wx.HSCROLL ), value )

    def isValid( self ):
        if not self.isPresent():
            return True

        text = self.value_ctrl.GetValue()
        if text.strip() == '':
            wx.MessageBox( T_('Enter a value for %s') % self.name,
                T_('Warning'), style=wx.OK|wx.ICON_EXCLAMATION )
            return False
        return True

    def getValue( self ):
        return self.value_ctrl.GetValue()

class SinglePropertyChoice(SingleProperty):
    def __init__( self, dialog, name, present, value, choices ):
        SingleProperty.__init__( self, dialog, name, present )

        ctrl = wx.Choice( self.dialog, self.value_id, choices=choices, size=(150,-1) )
        if self.was_present:
            ctrl.SetStringSelection( value )
        else:
            ctrl.SetStringSelection( choices[0] )
        self.setValueCtrl( ctrl, value )

    def getValue( self ):
        return self.value_ctrl.GetStringSelection()

class SinglePropertyNoValue(SingleProperty):
    def __init__( self, dialog, name, present ):
        SingleProperty.__init__( self, dialog, name, present )

        self.setValueCtrl( wx.StaticText( self.dialog, -1, '' ), '' )


new_name_id = wx.NewId()
new_value_id = wx.NewId()

class PropertiesDialogBase(wx.Dialog):
    def __init__( self, app, parent, path, prop_dict ):
        wx.Dialog.__init__( self, parent, -1, path )
        self.path = path
        self.prop_dict = prop_dict
        self.known_properties_names = []
        self.ignore_properties_names = []

    def initDialog( self ):
        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.property_ctrls = {}

        self.initKnownProperties()

        keys = self.prop_dict.keys()
        keys.sort()

        for prop in keys:
            if( prop not in self.known_properties_names
            and prop not in self.ignore_properties_names ):
                self.property_ctrls[ prop ] = SinglePropertyText( self, prop, True, self.prop_dict[ prop ] )

        self.new_name_ctrl  = wx.TextCtrl( self, new_name_id, '', size=(100,-1) )
        self.new_value_ctrl = wx.TextCtrl( self, new_value_id, '', size=(300,-1) )

        self.g_sizer.Add( self.new_name_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )
        self.g_sizer.Add( self.new_value_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 3 )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (300, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 15 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.g_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

    def OnOk( self, event ):
        for prop_ctrl in self.property_ctrls.values():
            if not prop_ctrl.isValid():
                return

        self.EndModal( wx.OK )

    def OnCancel( self, event ):
        self.EndModal( wx.CANCEL )

    def getModifiedProperties( self ):
        modified_properties = []
        for prop_ctrl in self.property_ctrls.values():
            if prop_ctrl.isModified():
                modified_properties.append(
                    (prop_ctrl.isPresent()
                    ,prop_ctrl.getName()
                    ,prop_ctrl.getValue()) )

        new_name = self.new_name_ctrl.GetValue()
        new_value = self.new_value_ctrl.GetValue()

        if new_name != '':
            modified_properties.append( (True, new_name, new_value) )
        return modified_properties

class FilePropertiesDialog(PropertiesDialogBase):
    def __init__( self, app, parent, path, prop_dict ):
        PropertiesDialogBase.__init__( self, app, parent, path, prop_dict )
        self.known_properties_names = ['svn:eol-style', 'svn:executable',
                                        'svn:mime-type', 'svn:needs-lock',
                                        'svn:keywords', 'svn:special']
        self.ignore_properties_names = ['svn:mergeinfo']
        self.initDialog()

    def initKnownProperties( self ):
        prop = 'svn:needs-lock'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, self.prop_dict.has_key( prop ) )

        prop = 'svn:executable'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, self.prop_dict.has_key( prop ) )

        # special is managed by SVN only the user must not change it
        prop = 'svn:special'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, self.prop_dict.has_key( prop ) )
        self.property_ctrls[ prop ].checkbox.Enable( False )

        prop = 'svn:eol-style'
        self.property_ctrls[ prop ] = SinglePropertyChoice( self, prop, self.prop_dict.has_key( prop ), 
                                self.prop_dict.get( prop, 'native' ), ['native','CRLF','LF','CR'] )
        prop = 'svn:mime-type'
        self.property_ctrls[ prop ] = SinglePropertyText( self, prop, self.prop_dict.has_key( prop ), 
                                self.prop_dict.get( prop, '' ) )

        prop = 'svn:keywords'
        self.property_ctrls[ prop ] = SinglePropertyText( self, prop, self.prop_dict.has_key( prop ), 
                                self.prop_dict.get( prop, '' ) )

class DirPropertiesDialog(PropertiesDialogBase):
    def __init__( self, app, parent, path, prop_dict ):
        PropertiesDialogBase.__init__( self, app, parent, path, prop_dict )
        self.known_properties_names = ['svn:ignore', 'svn:externals']
        self.ignore_properties_names = ['svn:mergeinfo']
        self.initDialog()

    def initKnownProperties( self ):
        prop = 'svn:ignore'
        self.property_ctrls[ prop ] = SinglePropertyMultiLine( self, prop, self.prop_dict.has_key( prop ), 
                                self.prop_dict.get( prop, '' ) )
        prop = 'svn:externals'
        self.property_ctrls[ prop ] = SinglePropertyMultiLine( self, prop, self.prop_dict.has_key( prop ), 
                                self.prop_dict.get( prop, '' ) )
