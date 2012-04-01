'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_show_diff_frame.py

'''

import wx
import wx.stc

import wb_config
import wb_diff_frame

class ShowDiffFrame(wx.Frame):
    def __init__( self, app, raw_text, title_left, title_right):
        self.app = app

        # fix up line endings CRLF to LF and CR to LF
        text = raw_text.replace( '\r\n', '\n' ).replace( '\r', '\n' )
        try:
            text = text.decode( 'utf-8' )
        except ValueError:
            pass

        diff_prefs = app.prefs.getDiffWindow()

        extra_style = 0
        if diff_prefs.maximized:
            extra_style = wx.MAXIMIZE
        wx.Frame.__init__( self, None, -1,
                T_("Diff %(title1)s and %(title2)s") %
                    {'title1': title_left
                    ,'title2': title_right},
                diff_prefs.frame_position,
                diff_prefs.getFrameSize(),
                wx.DEFAULT_FRAME_STYLE|extra_style )

        # Reset the size after startup to workaround a potential
        # problem on OSX with incorrect first size event saving the
        # wrong size in the preferences
        wx.CallAfter( self.SetSize, diff_prefs.getFrameSize() )

        text_control = wx.stc.StyledTextCtrl( self, -1,
                wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER )
        text_control.StyleSetSpec( wx.stc.STC_STYLE_DEFAULT, 
                "size:%d,face:%s,fore:#000000" % (wb_config.point_size, wb_config.face) )

        text_control.SetReadOnly( False )
        text_control.InsertText( 0, text )
        text_control.SetReadOnly( True )

        # Todo: should update the zoom value if the user changes it in this window...
        text_control.SetZoom( diff_prefs.zoom )
        
        self.CreateStatusBar()

        wx.EVT_SIZE( self, self.OnFrameSize )
        wx.EVT_MOVE( self, self.OnFrameMove )

        self.Show( True )

    def OnFrameSize( self, event ):
        pref = self.app.prefs.getDiffWindow()
        if not self.IsMaximized():
            pref.setFrameSize( self.GetSize() )

        event.Skip()

    def OnFrameMove( self, event ):
        pref = self.app.prefs.getDiffWindow()
        if not self.IsMaximized() and not self.IsIconized():
            # don't use the event.GetPosition() as it
            # is off by the window frame thinkness
            pt = self.GetPosition()
            pref.frame_position = pt

        pref.maximized = self.IsMaximized()

        event.Skip()
