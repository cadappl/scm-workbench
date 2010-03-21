'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_list_panel.py

'''
import wb_ids
import wb_list_panel_common

import wx

class WbListPanel(wb_list_panel_common.WbListPanelCommon):
    def __init__( self, app, frame, parent ):
        wb_list_panel_common.WbListPanelCommon.__init__( self, app, frame, parent )

    def __repr__( self ):
        return '<WbListPanel %r>' % self.list_handler

    def getAcceleratorTableInit( self ):
        acc_init =[
                (wx.ACCEL_CMD, ord('C'), wb_ids.id_SP_EditCopy),
                (wx.ACCEL_CMD, ord('X'), wb_ids.id_SP_EditCut),
                (wx.ACCEL_CMD, ord('V'), wb_ids.id_SP_EditPaste),

                (wx.ACCEL_CMD, ord('A'), wb_ids.id_SP_Add),
                (wx.ACCEL_CMD, ord('D'), wb_ids.id_SP_DiffWorkBase),
                (wx.ACCEL_CMD, ord('E'), wb_ids.id_File_Edit),
                (wx.ACCEL_CMD, ord('L'), wb_ids.id_SP_History),
                (wx.ACCEL_CMD, ord('I'), wb_ids.id_SP_Info),
                (wx.ACCEL_CMD, ord('P'), wb_ids.id_SP_Properties),
                (wx.ACCEL_CMD, ord('R'), wb_ids.id_SP_Revert),
                (wx.ACCEL_CMD, ord('T'), wb_ids.id_SP_UpdateTo),
                (wx.ACCEL_CMD, ord('U'), wb_ids.id_SP_Update),
                (wx.ACCEL_NORMAL, wx.WXK_DELETE, wb_ids.id_SP_Delete),
                (wx.ACCEL_CMD, ord('O'), wb_ids.id_Shell_Open),
                ]
        return acc_init
