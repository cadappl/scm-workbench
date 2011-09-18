'''
 ====================================================================
 Copyright (c) 2003-2007 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_diff_main.py

'''

VERSION_STRING = "Uncontrolled"

import sys

# make sure that we get 2.6 and not an earlier version
# 2.8 is reported to work as well
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select( ['2.9', '2.8', '2.6'] )

def noTranslate(msg):
    return msg

import __builtin__
__builtin__.__dict__['T_'] = noTranslate
__builtin__.__dict__['U_'] = noTranslate

import wx
import wb_diff_frame
import wb_preferences
import wb_platform_specific



class WbDiffApp:
    def __init__( self ):
        self.log = self
        self.prefs = wb_preferences.Preferences(
                self,
                wb_platform_specific.getPreferencesFilename(),
                wb_platform_specific.getOldPreferencesFilename() )

    def info( self, *arg ):
        pass

        
def main():
    if len(sys.argv) < 3:
        print 'Usages: wb_diff file1 file2'
        return 1

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    diff_app = WbDiffApp()
    app = wx.PySimpleApp()
    frame = wb_diff_frame.DiffFrame( diff_app, None, file1, file1, file2, file2 )

    frame.Show( True )
    app.MainLoop()
    return 0

if __name__ == '__main__':
    main()