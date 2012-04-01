'''
 ====================================================================
 Copyright (c) 2006-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_config.py

'''
import wx

#
#   Controls debug messages that help debug problems with
#   selection in tree and list controls
#
debug_selection = False
debug_selection_update = False

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

# control the experimental focus ring code
# that is not working yet
focus_ring = False

# default colours
colour_status_normal = wx.BLACK
colour_status_disabled = wx.Colour( 128, 128, 128 )
colour_status_unversioned = wx.Colour( 0, 112, 0 )
colour_status_locked = wx.RED
colour_status_need_checkout = wx.RED
colour_status_modified = wx.BLUE
colour_status_qqq = wx.BLUE

colour_log_normal = wx.BLACK
colour_log_tag = wx.BLUE
