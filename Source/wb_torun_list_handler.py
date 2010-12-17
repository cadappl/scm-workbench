'''
 ====================================================================
 Copyright (c) 2010 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_list_handler.py

'''

import wb_subversion_list_handler

class TorunListHandler(wb_subversion_list_handler.SubversionListHandler):
    def __init__( self, app, list_panel, project_info ):
        wb_subversion_list_handler.SubversionListHandler.__init__( self, app, list_panel, project_info )

