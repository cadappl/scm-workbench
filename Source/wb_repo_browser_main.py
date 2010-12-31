'''
 ====================================================================
 Copyright (c) 2010-2011, ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_repo_browser_main.py

'''

import sys

def noTranslate(msg):
    return msg

import __builtin__
__builtin__.__dict__['T_'] = noTranslate
__builtin__.__dict__['U_'] = noTranslate

import wx
import wb_preferences
import wb_platform_specific
import wb_repo_browser_frame


class WbRepoBrowserApp:
    def __init__( self ):
        self.log = self
        self.prefs = wb_preferences.Preferences(
                self,
                wb_platform_specific.getPreferencesFilename(),
                wb_platform_specific.getOldPreferencesFilename() )

    def getCredentials( self, realm, username, may_save ):
        # signature allows use a pysvn callback
        dialog = wb_dialogs.GetCredentials( self.frame, realm, username, may_save )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return (True, dialog.getUsername().encode('UTF-8'),
                dialog.getPassword().encode('UTF-8'), dialog.getSaveCredentials())
        else:
            return False, '', '', False

    def getServerTrust( self, realm, info_list, may_save ):
        # signature allows use a pysvn callback
        dialog = wb_dialogs.GetServerTrust( self.frame, realm, info_list, may_save )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            # Trust, save
            return True, dialog.getSaveTrust()
        else:
            # don't trust, don't save
            return False, False

    def setFrame( self, frame ):
        self.frame = frame

    def info( self, *arg ):
        pass

def main():
    repo_app = WbRepoBrowserApp()

    app = wx.PySimpleApp()
    frame = wb_repo_browser_frame.RepoBrowserFrame( None, repo_app )

    app.SetTopWindow( frame )
    repo_app.setFrame( frame )

    frame.Show( True )
    app.MainLoop()

    return 0

if __name__ == '__main__':
    main()
