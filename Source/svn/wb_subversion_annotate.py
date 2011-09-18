'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_annotate.py

'''
import wx
import time
import itertools

import wb_images
import wb_read_file
import wb_subversion_utils

class AnnotateFrame(wx.Frame):
    def __init__( self, app, project_info, filename, annotation ):
        wx.Frame.__init__( self, None, -1, T_("Annotation of %s") % filename )

        self.panel = AnnotatePanel( self, app, project_info, filename, annotation )

        # Set the application icon
        self.SetIcon( wb_images.getIcon( 'wb.png' ) )

        wx.EVT_CLOSE( self, self.OnCloseWindow )

    def OnCloseWindow( self, event ):
        self.Destroy()


class AnnotatePanel(wx.Panel):
    col_line = 0
    col_revision = 1
    col_author = 2
    col_date = 3
    col_text = 4

    def __init__( self, parent, app, project_info, filename, annotation ):
        wx.Panel.__init__( self, parent, -1 )

        self.app = app
        self.project_info = project_info
        self.filename = filename
        self.annotation = annotation

        self.id_list = wx.NewId()

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.list_ctrl = wx.ListCtrl( self, self.id_list, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT|wx.NO_BORDER)

        self.list_ctrl.InsertColumn( self.col_line, T_("Line") )
        self.list_ctrl.InsertColumn( self.col_revision, T_("Revision") )
        self.list_ctrl.InsertColumn( self.col_author, T_("Author") )
        self.list_ctrl.InsertColumn( self.col_date, T_("Date") )
        self.list_ctrl.InsertColumn( self.col_text, T_("Text") )

        char_width = 9
        self.list_ctrl.SetColumnWidth( self.col_line, 6*char_width )
        self.list_ctrl.SetColumnWidth( self.col_revision, 7*char_width )
        self.list_ctrl.SetColumnWidth( self.col_author, 14*char_width )
        self.list_ctrl.SetColumnWidth( self.col_date, 20*char_width )
        self.list_ctrl.SetColumnWidth( self.col_text, 250*char_width )

        self.v_sizer.Add( self.list_ctrl, 2, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_SIZE( self, self.OnSize )

        self.initList()

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

    #---------- Comment handlers ------------------------------------------------------------
    def OnSize( self, event):
        w,h = self.GetClientSizeTuple()
        self.v_sizer.SetDimension( 0, 0, w, h )

    def initList( self ):
        if len( self.annotation ) == 0:
            return

        encoding = wb_read_file.encodingFromContents( self.annotation[0]['line'] )

        last_revision = None

        all_row_colours = itertools.cycle(
                        (wx.Colour( 0xff, 0xff, 0xff )
                        ,wx.Colour( 0xf8, 0xf8, 0xf8 )
                        ) )

        row_colour = all_row_colours.next()

        for index, entry in enumerate( self.annotation ):
            raw_line = entry['line']
            try:
                line = raw_line.decode( encoding )

            except UnicodeDecodeError:
                # fall back to latin-1
                try:
                    line = raw_line.decode( 'iso8859-1' )
                except UnicodeDecodeError:
                    # sigh this is hard. use the choosen encoding and replace chars in error
                    line = raw_line.decode( encoding, 'replace' )

            if '\t' in line:
                column = 1
                char_list = []
                for c in line:
                    if c == '\t':
                        char_list.append( ' ' )
                        column += 1
                        while (column%8) != 0:
                            column += 1
                            char_list.append( ' ' )
                    else:
                        char_list.append( c )
                        column += 1
                tab_expanded_line = ''.join( char_list )
            else:
                tab_expanded_line = line

            self.list_ctrl.InsertStringItem( index, str(entry['number']+1) )

            if entry['revision'].number <= 0:
                revision = ' - '
            else:
                revision = str( entry['revision'].number )

            if revision != last_revision:
                # Only populate Revision, Author, Date columns when revision number changes.
                last_revision = revision
                row_colour = all_row_colours.next()

                entry_date = time.strptime( entry['date'].split('.')[0], '%Y-%m-%dT%H:%M:%S' )

                self.list_ctrl.SetStringItem( index, self.col_revision, revision )
                self.list_ctrl.SetStringItem( index, self.col_author, entry['author'] )
                self.list_ctrl.SetStringItem( index, self.col_date, wb_subversion_utils.fmtDateTime( entry_date ) )

            self.list_ctrl.SetStringItem( index, self.col_text, tab_expanded_line )

            self.list_ctrl.SetItemBackgroundColour( index, row_colour )
