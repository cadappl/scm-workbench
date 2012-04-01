'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_frame.py

'''
import threading
import wx
import wx.stc

import wb_diff_images
import wb_diff_difflib
import wb_diff_processor

id_expand_folds_command = wx.NewId()
id_collapse_folds_command = wx.NewId()
id_whitespace_command = wx.NewId()
id_previous_command = wx.NewId()
id_next_command = wx.NewId()

# point size and face need to choosen for platform
if wx.Platform == '__WXMSW__':
    face = 'Courier New'
    point_size = 8

elif wx.Platform == '__WXMAC__':
    face = 'Monaco'
    point_size = 12

else:
    face = 'Courier'
    point_size = 12

class DiffFrame(wx.Frame):
    def __init__( self, app, parent, file_left, title_left, file_right, title_right ):
        self.app = app

        diff_prefs = self.app.prefs.getDiffWindow()

        extra_style = 0
        if diff_prefs.maximized:
            extra_style = wx.MAXIMIZE

        wx.Frame.__init__(self, None, -1, T_("Diff %(title1)s and %(title2)s") %
                            {'title1': title_left
                            ,'title2': title_right},
                diff_prefs.frame_position,
                diff_prefs.getFrameSize(),
                wx.DEFAULT_FRAME_STYLE|extra_style )

        # Reset the size after startup to workaround a potential
        # problem on OSX with incorrect first size event saving the
        # wrong size in the preferences
        wx.CallAfter( self.SetSize, diff_prefs.getFrameSize() )

        # Set up the toolbar
        self.toolbar = self.CreateToolBar( wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT )

        self.toolbar.AddSimpleTool( id_expand_folds_command, wb_diff_images.getExpandBitmap(), T_("Expand folds"), T_("Expand all folds") )
        self.toolbar.AddSimpleTool( id_collapse_folds_command, wb_diff_images.getCollapseBitmap(), T_("Collapse folds"), T_("Collapse all folds") )
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool( id_whitespace_command, wb_diff_images.getWhiteSpaceBitmap(), T_("Toggle whitespace"), T_("Show/hide whitespace") )
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool( id_previous_command, wb_diff_images.getUpArrowBitmap(), T_("Previous difference"), T_("Positions the cursor at the previous difference between the files") )
        self.toolbar.AddSimpleTool( id_next_command, wb_diff_images.getDownArrowBitmap(), T_("Next difference"), T_("Positions the cursor at the next difference between the files") )

        self.toolbar.Realize()

        # Set the application icon
        self.SetIcon( wb_diff_images.getAppIconIcon() )

        # Add the status bar
        self.status_bar_size_changed = False

        s = self.CreateStatusBar()

        s.SetFieldsCount( 3 )
        s.SetStatusWidths( [-1, 380, 10] )

        self.total_change_number = 0
        self.current_change_number = 0
        self.setChangeCounts( 0, 0 )

        self.status_bar_key_field = DiffBodyText( s )
        self.status_bar_key_field.InsertStyledText( T_('Key: '), self.status_bar_key_field.style_line_normal )
        self.status_bar_key_field.InsertStyledText( T_('Inserted text '), self.status_bar_key_field.style_line_insert )
        self.status_bar_key_field.InsertStyledText( T_('Deleted text '), self.status_bar_key_field.style_line_delete )
        self.status_bar_key_field.InsertStyledText( T_('Changed text'), self.status_bar_key_field.style_line_changed )
        self.status_bar_key_field.SetReadOnly( True )
        self.status_bar_key_field.Enable( False )

        self._repositionStatusBar()

        wx.EVT_SIZE( s, self.OnStatusBarSize )
        wx.EVT_IDLE( s, self.OnStatusBarIdle )

        # Set up the splitter window with the editor panels
        self.splitter = wx.SplitterWindow( self, -1 )
        self.sash_ratio = 0.5

        self.panel_left = DiffPanel( self.splitter, title_left )
        self.panel_right = DiffPanel( self.splitter, title_right )

        self.panel_left.ed.SetMirrorEditor( self.panel_right.ed )
        self.panel_right.ed.SetMirrorEditor( self.panel_left.ed )

        self.splitter.SetMinimumPaneSize( 150 )
        self.splitter.SplitVertically( self.panel_left, self.panel_right )
        self.splitter.SetSashPosition( 150 )

        # Create the editor and calculate all the differences
        self.processor = wb_diff_processor.DiffProcessor( self.panel_left.ed, self.panel_right.ed )
        self.diff = wb_diff_difflib.Difference( self.processor )


        self.files_ok = self.diff.filecompare( file_left, file_right )
        if not self.files_ok:
            return

        self.setChangeCounts( None, self.processor.getChangeCount() )
        self.SetZoom( diff_prefs.zoom )

        # Move to the first change in the editor.
        event = wx.CommandEvent( wx.wxEVT_COMMAND_TOOL_CLICKED, id_next_command )
        self.GetEventHandler().AddPendingEvent( event )

        # Set up the keyboard shortcuts
        accelerator_table = wx.AcceleratorTable(
            [(wx.ACCEL_NORMAL, ord('p'), id_previous_command )
            ,(wx.ACCEL_SHIFT,  wx.WXK_F7, id_previous_command )
            ,(wx.ACCEL_NORMAL, ord('n'), id_next_command )
            ,(wx.ACCEL_NORMAL, wx.WXK_F7, id_next_command )
            ,(wx.ACCEL_NORMAL, ord(' '), id_whitespace_command )
            ,(wx.ACCEL_NORMAL, ord('e'), id_expand_folds_command )
            ,(wx.ACCEL_NORMAL, ord('c'), id_collapse_folds_command )
            ])
        self.SetAcceleratorTable( accelerator_table )

        wx.EVT_CLOSE( self, self.OnCloseWindow )
        wx.EVT_SIZE( self.splitter, self.OnSize )
        wx.EVT_SPLITTER_SASH_POS_CHANGED( self.splitter, -1, self.OnSashPositionChanged )
        wx.EVT_TOOL( self, id_previous_command, self.OnToolUpArrow )
        wx.EVT_TOOL( self, id_next_command, self.OnToolDownArrow )
        wx.EVT_TOOL( self, id_whitespace_command, self.OnToolWhitespace )
        wx.EVT_TOOL( self, id_expand_folds_command, self.OnToolExpandFolds )
        wx.EVT_TOOL( self, id_collapse_folds_command, self.OnToolCollapseFolds )

        wx.EVT_SIZE( self, self.OnFrameSize )
        wx.EVT_MOVE( self, self.OnFrameMove )

        wx.stc.EVT_STC_ZOOM( self, self.panel_left.ed.GetId(), self.OnZoomChange )
        wx.stc.EVT_STC_ZOOM( self, self.panel_right.ed.GetId(), self.OnZoomChange )


    def isOk( self ):
        return self.files_ok

    #------------------------------------------------------------
    def OnStatusBarSize( self, event ):
        self._repositionStatusBar()

        # tell idle to fix up status bar
        self.status_bar_size_changed = True

    def OnStatusBarIdle( self, event ):
        if self.status_bar_size_changed:
            self._repositionStatusBar()
            self.status_bar_size_changed = False

    def setChangeCounts( self, current_change_number=None, total_change_number=None ):
        if current_change_number is not None:
            self.current_change_number = current_change_number
        if total_change_number is not None:
            self.total_change_number = total_change_number

        self.SetStatusText( T_('Diff %(change1)d of %(change2)d') %
                                {'change1': self.current_change_number
                                ,'change2': self.total_change_number}, 2 )

    def _repositionStatusBar(self):
        rect = self.GetStatusBar().GetFieldRect( 1 )
        self.status_bar_key_field.SetPosition(wx.Point(rect.x+2, rect.y+2))
        self.status_bar_key_field.SetSize(wx.Size(rect.width-4, rect.height-4))

    #------------------------------------------------------------
    def OnCloseWindow( self, event ):
        diff_prefs = self.app.prefs.getDiffWindow()
        # Size and Position are already saved
        diff_prefs.maximized = self.IsMaximized()

        self.Destroy()

    def OnSashPositionChanged( self, event ):
        w, h = self.splitter.GetClientSizeTuple()
        self.sash_ratio = float( event.GetSashPosition() ) / float( w )
        event.Skip()

    def OnSize( self, event ):
        w, h = self.splitter.GetClientSizeTuple()
        self.splitter.SetSashPosition( int(w * self.sash_ratio) )
        event.Skip()

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

    def OnToolDownArrow( self, event ):
        if self.total_change_number == 0:
            return
        self.processor.moveNextChange()
        self.setChangeCounts( self.processor.getCurrentChange() )

    def OnToolUpArrow( self, event ):
        if self.total_change_number == 0:
            return
        self.processor.movePrevChange()
        self.setChangeCounts( self.processor.getCurrentChange() )

    def OnToolWhitespace( self, event ):
        self.panel_left.ed.ToggleViewWhiteSpace()
        self.panel_right.ed.ToggleViewWhiteSpace()

    def OnToolExpandFolds( self, event ):
        self.showAllFolds( True )

    def OnToolCollapseFolds( self, event ):
        self.showAllFolds( False )

    def showAllFolds( self, show ):
        self.panel_left.ed.ShowAllFolds( show )
        self.panel_right.ed.ShowAllFolds( show )

    def OnZoomChange( self, evt ):
        zoom = evt.GetEventObject().GetZoom()
        self.SetZoom( zoom )
        diff_prefs = self.app.prefs.getDiffWindow()
        diff_prefs.zoom = zoom
        
    def SetZoom( self, zoom ):
        if zoom != self.panel_left.ed.GetZoom():
            self.panel_left.ed.SetZoom( zoom )

        if zoom != self.panel_right.ed.GetZoom():
            self.panel_right.ed.SetZoom( zoom )

        self.panel_left.ed.diff_line_numbers.SetZoom( zoom )
        self.panel_right.ed.diff_line_numbers.SetZoom( zoom )
            
#----------------------------------------------------------------------

WB_EVT_SYNC_SCROLL_type = wx.NewEventType()

def WB_EVT_SYNC_SCROLL( window, id, handler ):
    window.Connect( id, -1, WB_EVT_SYNC_SCROLL_type, handler )

class SyncScrollEvent(wx.PyCommandEvent):
    'SyncScrollEvent'
    def __init__(self, id, text_body_this, test_body_other):
        wx.PyCommandEvent.__init__(self, WB_EVT_SYNC_SCROLL_type, id)

        self.text_body_this = text_body_this
        self.test_body_other = test_body_other

#----------------------------------------------------------------------

class DiffPanel(wx.Panel):
    ''' DiffPanel '''
    def __init__( self, parent_win, title ):
        wx.Panel.__init__( self, parent_win, -1 )

        self.SetSize(wx.Size(200, 200))

        self.text_file_name = wx.TextCtrl(self, -1, title,
                        wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )

        self.ed = DiffBodyText( self )


        box_diffs = wx.BoxSizer( wx.VERTICAL )
        box_diffs.Add( self.ed, 1, wx.EXPAND )

        box_line_numbers = wx.BoxSizer( wx.HORIZONTAL )
        box_line_numbers.Add( self.ed.diff_line_numbers, 0, wx.EXPAND )
        box_line_numbers.Add( box_diffs, 1, wx.EXPAND )

        box_file_name = wx.BoxSizer( wx.VERTICAL )
        box_file_name.Add( self.text_file_name, 0, wx.EXPAND )
        box_file_name.Add( box_line_numbers, 1, wx.EXPAND )

        box_file_name.Fit( self )

        self.SetAutoLayout( True )
        self.SetSizer( box_file_name )

#------------------------------------------------------------------------------------------
class DiffBodyText(wx.stc.StyledTextCtrl):
    def __init__(self, parent):

        self.test_body_other = None

        wx.stc.StyledTextCtrl.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER)

        self.diff_line_numbers = DiffLineNumbers( parent )

        # Calculate space for 5 digits
        font = wx.Font(point_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, face)
        width, _, _, _ = self.diff_line_numbers.GetFullTextExtent('12345', font)

        width = width + 10
        self.diff_line_numbers.SetSize( wx.Size( width, 200 ) )
        # starting with 2.5.2.? we have to set the hint
        self.diff_line_numbers.SetSizeHints( minW=width, maxW=width, maxH=-1, minH=-1 )
        self.diff_line_numbers.Enable( False )

        # Hide the scrollbars for the line number edit control
        scrollbar = wx.ScrollBar( self, -1, style = wx.SB_VERTICAL )
        self.diff_line_numbers.SetVScrollBar( scrollbar )
        scrollbar.Show( False )
        self.diff_line_numbers.SetUseHorizontalScrollBar( False )

        self.diff_line_numbers.StyleSetSpec( wx.stc.STC_STYLE_DEFAULT,
                "size:%d,face:%s,fore:#000000,back:#e0e0e0" % (point_size, face) )

        self.fold_margin = -1
        self.fold_start = -1
        self.fold_context_border = 1
        self.fold_minimum_length = self.fold_context_border * 2 + 1

        self.style_line_normal = 0
        self.style_line_insert = 1
        self.style_line_delete = 2
        self.style_line_changed = 3

        self.style_replace_insert =  self.style_line_insert | wx.stc.STC_INDIC1_MASK
        self.style_replace_delete =  self.style_line_delete | wx.stc.STC_INDIC1_MASK
        self.style_replace_changed = self.style_line_changed | wx.stc.STC_INDIC1_MASK
        self.style_replace_equal =   self.style_line_normal | wx.stc.STC_INDIC1_MASK

        self.EmptyUndoBuffer()

        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)

        self.SetScrollWidth(10000)

        # make some styles
        self.StyleSetSpec( wx.stc.STC_STYLE_DEFAULT,
                "size:%d,face:%s,fore:#000000" % (point_size, face) )
        self.StyleSetSpec( self.style_line_insert, "fore:#008200" )
        self.StyleSetSpec( self.style_line_delete, "fore:#0000FF" )
        self.StyleSetSpec( self.style_line_changed, "fore:#FF0000" )

        # and finally, an indicator or two
        self.IndicatorSetStyle( self.style_line_insert, wx.stc.STC_INDIC_SQUIGGLE )
        self.IndicatorSetForeground( self.style_line_insert, wx.Colour(0xff, 0xb0, 0xb0) )
        self.IndicatorSetStyle( self.style_line_delete, wx.stc.STC_INDIC_SQUIGGLE)
        self.IndicatorSetForeground( self.style_line_delete, wx.Colour(0xff, 0x00, 0x00) )
        self.IndicatorSetStyle( self.style_line_changed, wx.stc.STC_INDIC_STRIKE )
        self.IndicatorSetForeground( self.style_line_changed, wx.BLACK )

        wx.stc.EVT_STC_MARGINCLICK( self, -1, self.OnMarginClick )

        self.SetupFolding( 1 )

        wx.EVT_MOUSEWHEEL( self, self.OnMouseWheel )
        wx.EVT_SCROLLWIN( self, self.OnNeedToSyncScroll )
        wx.stc.EVT_STC_UPDATEUI( self, -1, self.OnNeedToSyncScroll )
        WB_EVT_SYNC_SCROLL( self, -1, self.OnSyncScroll )
        DiffBodyText.body_count += 1
        self.body_count = DiffBodyText.body_count

    body_count = 0
    def __str__( self ):
        return '<DiffBodyText: %d>' % self.body_count

    def OnMouseWheel( self, event ):
        assert( self.test_body_other )
        self.GetEventHandler().AddPendingEvent( SyncScrollEvent( self.GetId(), self, self.test_body_other ) )
        event.Skip()

    def OnNeedToSyncScroll( self, event ):
        if self.test_body_other is not None:
            
            self.GetEventHandler().AddPendingEvent( SyncScrollEvent( self.GetId(), self, self.test_body_other ) )
        event.Skip()

    def OnSyncScroll( self, event ):
        line_number = event.text_body_this.GetFirstVisibleLine()
        event.test_body_other.ScrollToLine( line_number )
        event.test_body_other.diff_line_numbers.ScrollToLine( line_number )
        event.text_body_this.diff_line_numbers.ScrollToLine( line_number )
        
        xpos = event.text_body_this.GetXOffset()
        event.test_body_other.SetXOffset( xpos )
        sb_horizontal_postion = event.text_body_this.GetScrollPos( wx.SB_HORIZONTAL )
        if event.test_body_other.GetScrollPos( wx.SB_HORIZONTAL ) != sb_horizontal_postion:
            event.test_body_other.SetScrollPos( wx.SB_HORIZONTAL, sb_horizontal_postion, True )

    def SetMirrorEditor( self, test_body_other ):
        self.test_body_other = test_body_other

    def ToggleViewWhiteSpace( self ):
        if self.GetViewWhiteSpace():
            self.SetViewWhiteSpace( False )
        else:
            self.SetViewWhiteSpace( True )

    #--------------------------------------------------------------------------------
    def OnMarginClick( self, event ):
        if event.GetMargin() == self.fold_margin:
            self.ToggleFoldAtLine( self.LineFromPosition( event.GetPosition() ) )

    #--------------------------------------------------------------------------------
    def InsertStyledText( self, text, style ):
        pos = self.GetLength()
        self.InsertText( pos, text )
        self.StartStyling( pos, 0xff )
        self.SetStyling( len(text), style )

    def ChangeLineStyle( self, line, style ):
        pos_start = self.PositionFromLine( line )
        pos_end = self.GetLineEndPosition( line )
        self.StartStyling( pos_start, 0xff )

        self.SetSelection( pos_start, pos_end )
        text = self.GetSelectedText()
        self.ReplaceSelection(text)
        self.SetSelection( -1, -1 )

        self.SetStyling( pos_end - pos_start, style )

    #--------------------------------------------------------------------------------
    def SetupFolding( self, margin ):
        self.fold_margin = margin
        self.SetProperty( "fold", "1" )
        self.diff_line_numbers.SetProperty( "fold", "1" )
        self.SetMarginType( self.fold_margin, wx.stc.STC_MARGIN_SYMBOL )

        self.SetMarginMask( self.fold_margin, wx.stc.STC_MASK_FOLDERS )
        self.SetMarginSensitive( self.fold_margin, True )
        self.SetMarginWidth( self.fold_margin, 15 )

        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "black" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,  "white", "black" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,  "white", "grey" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,    "white", "grey" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,  "white", "black" )
        self.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS, "white", "black" )

    def ToggleFoldAtLine( self, line ):
        if self.GetFoldLevel( line ) & wx.stc.STC_FOLDLEVELHEADERFLAG:
            if self.GetFoldExpanded( line ):
                self.SetFoldExpanded( line, False )
                self.diff_line_numbers.SetFoldExpanded( line, False )
                self._ShowFoldLines( line, self.GetFoldEnd( line ), False )
            else:
                self.SetFoldExpanded( line, True)
                self.diff_line_numbers.SetFoldExpanded( line, True )
                self._ShowFoldLines( line, self.GetFoldEnd( line ), True )

    def GetFoldEnd( self, fold_start_line ):
        current_fold_line = fold_start_line

        fold_level = self.GetFoldLevel( current_fold_line ) & wx.stc.STC_FOLDLEVELNUMBERMASK

        while (self.GetFoldLevel( current_fold_line ) & wx.stc.STC_FOLDLEVELNUMBERMASK) >= fold_level:
            current_fold_line = current_fold_line + 1

        return current_fold_line - 1

    def _ShowFoldLines( self, start_line, end_line, show_lines ):
        fold_start = start_line + self.fold_context_border
        fold_end = end_line - self.fold_context_border

        self.ShowFoldLines( fold_start, fold_end, show_lines )

    def ShowFoldLines( self, start_line, end_line, show_lines ):
        if show_lines:
            self.ShowLines( start_line, end_line )
            self.diff_line_numbers.ShowLines( start_line, end_line )
        else:
            self.HideLines( start_line, end_line )
            self.diff_line_numbers.HideLines( start_line, end_line )

    def SetFoldLine(self, line_number, is_fold_line):
        if is_fold_line:
            if self.fold_start == -1:
                self.fold_start = line_number
            elif line_number - self.fold_start == self.fold_minimum_length:
                self.SetFoldLevel( self.fold_start, (wx.stc.STC_FOLDLEVELBASE+1) | wx.stc.STC_FOLDLEVELHEADERFLAG )
                self.diff_line_numbers.SetFoldLevel( self.fold_start, (wx.stc.STC_FOLDLEVELBASE+1) | wx.stc.STC_FOLDLEVELHEADERFLAG )

            self.SetFoldLevel( line_number, wx.stc.STC_FOLDLEVELBASE+1 )
            self.diff_line_numbers.SetFoldLevel( line_number, wx.stc.STC_FOLDLEVELBASE+1 )
        else:
            self.SetFoldLevel( line_number, wx.stc.STC_FOLDLEVELBASE )
            self.diff_line_numbers.SetFoldLevel( line_number, wx.stc.STC_FOLDLEVELBASE )
            if self.fold_start != -1:
                self.fold_start = -1

    def ShowAllFolds(self, show_folds):
        for line in range(self.GetLineCount()):
            if( self.GetFoldLevel( line ) & wx.stc.STC_FOLDLEVELHEADERFLAG
            and ((self.GetFoldExpanded( line ) and not show_folds)
            or (not self.GetFoldExpanded( line ) and show_folds)) ):
                self.ToggleFoldAtLine( line )

#------------------------------------------------------------------------------------------
class DiffLineNumbers(wx.stc.StyledTextCtrl):
    def __init__(self, parent):

        wx.stc.StyledTextCtrl.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER)

        self.style_line_numbers = 0
        self.style_line_numbers_for_diff = 1

        self.EmptyUndoBuffer()

        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)

        self.SetScrollWidth(10000)

        # make some styles
        self.StyleSetSpec( wx.stc.STC_STYLE_DEFAULT,
                "size:%d,face:%s,fore:#000000" % (point_size, face) )
        self.StyleSetSpec( self.style_line_numbers,
                "size:%d,face:%s,fore:#000000,back:#f0f0f0" % (point_size, face) )
        self.StyleSetSpec( self.style_line_numbers_for_diff,
                "size:%d,face:%s,fore:#000000,back:#d0d0d0" % (point_size, face) )

    #--------------------------------------------------------------------------------
    def InsertStyledText( self, text, style ):
        pos = self.GetLength()
        self.InsertText( pos, text )
        self.StartStyling( pos, 0xff )
        self.SetStyling( len(text), style )

    def ChangeLineStyle( self, line, style ):
        pos_start = self.PositionFromLine( line )
        pos_end = self.GetLineEndPosition( line )
        self.StartStyling( pos_start, 0xff )

        self.SetSelection( pos_start, pos_end )
        text = self.GetSelectedText()
        self.ReplaceSelection(text)
        self.SetSelection( -1, -1 )

        self.SetStyling( pos_end - pos_start, style )
