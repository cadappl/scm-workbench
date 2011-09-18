'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_dialogs.py

'''

import wx

import pysvn
import wb_subversion_utils

class UpdateTo(wx.Dialog):
    def __init__( self, parent, title ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.all_depth_types =  [(pysvn.depth.empty,        T_('Empty directory'))
                               #,(pysvn.depth.exclude,      T_('Exclude (not used yet)'))
                                ,(pysvn.depth.files,        T_('Children files only'))
                                ,(pysvn.depth.immediates,   T_('Immediate children'))
                                ,(pysvn.depth.unknown,      T_('Only already checked out descendants'))
                                ,(pysvn.depth.infinity,     T_('All descendants (Full recursion)'))]

        self.depth_enabled = wb_subversion_utils.version_info.has_depth

        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.revision_border = wx.StaticBox( self, -1, title )
        self.revision_box = wx.StaticBoxSizer( self.revision_border, wx.VERTICAL )

        # Line 1: checkbox for head revision
        self.head_checkbox_ctrl = wx.CheckBox( self, -1, T_("HEAD revision") )
        self.head_checkbox_ctrl.SetValue( True )

        self.revision_box.Add( self.head_checkbox_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        # Line 2: text entry for giving a revision no. manually
        self.revision_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.revision_text = wx.StaticText( self, -1, T_('Revision:') )
        self.revision_ctrl = wx.TextCtrl( self, -1, '' )
        self.revision_ctrl.SetSelection( -1, -1 )
        self.revision_ctrl.Enable( False )

        self.g_sizer.Add( self.revision_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.revision_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        if self.depth_enabled:
            self.r_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
            self.r_sizer.AddGrowableCol( 1 )

            self.recursive_border = wx.StaticBox( self, -1, T_('Apply on') )
            self.recursive_box = wx.StaticBoxSizer( self.recursive_border, wx.VERTICAL )

            self.recursive_checkbox_ctrl = wx.CheckBox( self, -1, T_('Recursive (all)') )
            self.recursive_checkbox_ctrl.SetValue( True )

            self.recursive_box.Add( self.recursive_checkbox_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
            self.recursive_box.Add( self.r_sizer, 0, wx.EXPAND )

            self.depth_text = wx.StaticText( self, -1, T_('Depth:') )
            self.depth_ctrl = wx.Choice( self, -1, choices=[name for depth, name in self.all_depth_types] )
            for index, (depth, name) in enumerate( self.all_depth_types ):
                if depth == pysvn.depth.unknown:
                    self.depth_ctrl.SetSelection( index )
            self.depth_ctrl.Enable( False )

            self.r_sizer.Add( self.depth_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
            self.r_sizer.Add( self.depth_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        # Line 3: Ok/Cancel button
        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.revision_box, 0, wx.EXPAND|wx.ALL, 5 )
        if self.depth_enabled:
            self.v_sizer.Add( self.recursive_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        # Catch button events
        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

        # Catch checkbox events
        wx.EVT_CHECKBOX ( self, self.head_checkbox_ctrl.GetId(), self.onHeadRevisionClicked )
        if self.depth_enabled:
            wx.EVT_CHECKBOX ( self, self.recursive_checkbox_ctrl.GetId(), self.recursiveClicked )


    def OnOk( self, event ):
        # Check revision value
        if not self.head_checkbox_ctrl.GetValue():
            try:
                val = int( self.revision_ctrl.GetValue() )
                if val < 1:
                    wx.MessageBox( T_('Please enter a revision number > 0!'),
                                   style=wx.OK|wx.ICON_ERROR )
                    return

            except ValueError:
                wx.MessageBox( T_('Please enter digits only!'),
                                style=wx.OK|wx.ICON_ERROR )
                return

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def onHeadRevisionClicked( self, event ):
        self.revision_ctrl.Enable( not self.head_checkbox_ctrl.GetValue() )

    def getRevision( self ):
        if self.head_checkbox_ctrl.GetValue():
            return pysvn.Revision( pysvn.opt_revision_kind.head )
        else:
            rev = int( self.revision_ctrl.GetValue() )
            return pysvn.Revision( pysvn.opt_revision_kind.number, rev )

    def getSvnDepth( self ):
        if self.depth_enabled:
            return (self.getRecursive(), self.getDepth( pysvn.depth.unknown ))
        else:
            return (True, None)

    def recursiveClicked( self, event ):
        self.depth_ctrl.Enable( not self.recursive_checkbox_ctrl.GetValue() )

    def getRecursive( self ):
        return self.recursive_checkbox_ctrl.GetValue()

    def getDepth( self, default ):
        if self.recursive_checkbox_ctrl.GetValue():
            return default
        else:
            return self.all_depth_types[ self.depth_ctrl.GetSelection() ][0]

class Switch(wx.Dialog):
    def __init__( self, parent, app, wc_path, title, curr_url='' ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.app = app
        self.parent = parent

        self.all_depth_types =  [(pysvn.depth.empty,        T_('Empty directory'))
                               #,(pysvn.depth.exclude,      T_('Exclude (not used yet)'))
                                ,(pysvn.depth.files,        T_('Children files only'))
                                ,(pysvn.depth.immediates,   T_('Immediate children'))
                                ,(pysvn.depth.unknown,      T_('Only already checked out descendants'))
                                ,(pysvn.depth.infinity,     T_('All descendants (Full recursion)'))]

        self.depth_enabled = wb_subversion_utils.version_info.has_depth

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        # Line 1: Switch
        self.v_sizer.Add( wx.StaticText( self, -1, T_('Switch') ), 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( wx.StaticText( self, -1, wc_path ), 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( wx.StaticText( self, -1 ))

        # Line 2: ToURL
        self.tourl_ctrl = wx.TextCtrl( self, -1, curr_url )
        self.tourl_button = wx.Button( self, -1, '...' )
        self.v_sizer.Add( wx.StaticText( self, -1, T_('To URL') ), 0, wx.EXPAND|wx.ALL, 5 )

        g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        g_sizer.AddGrowableCol( 0 )
        g_sizer.Add( self.tourl_ctrl, 1, wx.EXPAND|wx.ALL )
        g_sizer.Add( self.tourl_button, 0, wx.ALIGN_RIGHT )
        self.v_sizer.Add( g_sizer, 1, wx.EXPAND|wx.ALL, 5 )

        self.revision_border = wx.StaticBox( self, -1, T_('Revision') )
        self.revision_box = wx.StaticBoxSizer( self.revision_border, wx.VERTICAL )

        # Line 3: checkbox for head revision
        self.head_checkbox_ctrl = wx.CheckBox( self, -1, T_('HEAD revision') )
        self.head_checkbox_ctrl.SetValue( True )

        self.revision_box.Add( self.head_checkbox_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        # Line 4: text entry for giving a revision no. manually
        self.g_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.revision_box.Add( self.g_sizer, 0, wx.EXPAND )

        self.revision_text = wx.StaticText( self, -1, T_('Revision:') )
        self.revision_ctrl = wx.TextCtrl( self, -1 )
        self.revision_ctrl.SetSelection( -1, -1 )
        self.revision_ctrl.Enable( False )

        self.g_sizer.Add( self.revision_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.revision_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        if self.depth_enabled:
            self.r_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
            self.r_sizer.AddGrowableCol( 1 )

            self.recursive_border = wx.StaticBox( self, -1, T_('Apply on') )
            self.recursive_box = wx.StaticBoxSizer( self.recursive_border, wx.VERTICAL )

            self.recursive_checkbox_ctrl = wx.CheckBox( self, -1, T_('Recursive (all)') )
            self.recursive_checkbox_ctrl.SetValue( True )

            self.recursive_box.Add( self.recursive_checkbox_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
            self.recursive_box.Add( self.r_sizer, 0, wx.EXPAND )

            self.depth_text = wx.StaticText( self, -1, T_('Depth:') )
            self.depth_ctrl = wx.Choice( self, -1, choices=[name for depth, name in self.all_depth_types] )
            for index, (depth, name) in enumerate( self.all_depth_types ):
                if depth == pysvn.depth.unknown:
                    self.depth_ctrl.SetSelection( index )
            self.depth_ctrl.Enable( False )

            self.r_sizer.Add( self.depth_text, 1, wx.EXPAND|wx.NORTH|wx.ALIGN_RIGHT, 5 )
            self.r_sizer.Add( self.depth_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        # Line 5: Ok/Cancel button
        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (150, 20), 1, wx.EXPAND )
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.revision_box, 0, wx.EXPAND|wx.ALL, 5 )
        if self.depth_enabled:
            self.v_sizer.Add( self.recursive_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        # Catch button events
        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )
        wx.EVT_BUTTON( self, self.tourl_button.GetId(), self.OnEventTourlButton )

        # Catch checkbox events
        wx.EVT_CHECKBOX ( self, self.head_checkbox_ctrl.GetId(), self.onHeadRevisionClicked )
        if self.depth_enabled:
            wx.EVT_CHECKBOX ( self, self.recursive_checkbox_ctrl.GetId(), self.recursiveClicked )

    def OnEventTourlButton( self, event ):
        new_url = self.parent.app.getRepositoryPath( self.parent,
                                                     self.tourl_ctrl.GetValue() )
        if new_url:
            self.tourl_ctrl.SetValue( new_url )

    def OnOk( self, event ):
        if not self.tourl_ctrl.GetValue():
            wx.MessageBox( T_('Please enter a URL to switch'),
                           style=wx.OK|wx.ICON_ERROR )
            return

        # Check revision value
        if not self.head_checkbox_ctrl.GetValue():
            try:
                val = int( self.revision_ctrl.GetValue() )
                if val < 1:
                    wx.MessageBox( T_('Please enter a revision number > 0!'),
                                   style=wx.OK|wx.ICON_ERROR )
                    return

            except ValueError:
                wx.MessageBox( T_('Please enter digits only!'),
                                style=wx.OK|wx.ICON_ERROR )
                return

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def onHeadRevisionClicked( self, event ):
        self.revision_ctrl.Enable( not self.head_checkbox_ctrl.GetValue() )

    def getRevision( self ):
        if self.head_checkbox_ctrl.GetValue():
            return pysvn.Revision( pysvn.opt_revision_kind.head )
        else:
            rev = int( self.revision_ctrl.GetValue() )
            return pysvn.Revision( pysvn.opt_revision_kind.number, rev )

    def getSvnDepth( self ):
        if self.depth_enabled:
            return self.getRecursive(), self.getDepth( pysvn.depth.unknown )
        else:
            return True, None

    def getValues( self ):
        return self.tourl_ctrl.GetValue().strip(), self.getSvnDepth()

    def recursiveClicked( self, event ):
        self.depth_ctrl.Enable( not self.recursive_checkbox_ctrl.GetValue() )

    def getRecursive( self ):
        return self.recursive_checkbox_ctrl.GetValue()

    def getDepth( self, default ):
        if self.recursive_checkbox_ctrl.GetValue():
            return default
        else:
            return self.all_depth_types[ self.depth_ctrl.GetSelection() ][0]
