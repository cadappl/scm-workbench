'''
 ====================================================================
 Copyright (c) 2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_toolbars.py

'''
import wb_ids
import wb_images

class ToolBarResource:
    def __init__( self ):
        self.__all_groups = []
        self.__all_group_contents = {}
        self.__all_buttons = {}

        self.__last_group = None

    def addButton( self, button_id, bitmap, short_help, long_help=None, is_toggle=False ):
        self.__all_buttons[ button_id ] = ToolBarButtonInfo( button_id, bitmap, short_help, long_help, is_toggle )

    def getButtonById( self, button_id ):
        return self.__all_buttons[ button_id ]

    def addGroup( self, group_name ):
        self.__all_groups.append( group_name )
        self.__all_group_contents[ group_name ] = []

        self.__last_group = group_name

        return self

    def addToGroup( self, button_id ):
        self.__all_group_contents[ self.__last_group ].append( button_id )
        return self

    def getAllGroupNames( self ):
        return self.__all_groups[:]

    def populateToolBar( self, toolbar_prefs, toolbar ):
        may_add_separator = False

        for group_name in toolbar_prefs.group_order:
            all_group_contents = self.__all_group_contents[ group_name ]

            if( len( all_group_contents ) > 0
            and may_add_separator ):
                toolbar.AddSeparator()

            for button_id in all_group_contents:
                button = self.__all_buttons[ button_id ]

                toolbar.AddSimpleTool(
                        button.button_id,
                        wb_images.getBitmap( button.bitmap, (toolbar_prefs.bitmap_size,toolbar_prefs.bitmap_size) ),
                        T_(button.short_help),
                        T_(button.long_help),
                        isToggle=button.is_toggle
                        )

            may_add_separator = True

class ToolBarButtonInfo:
    def __init__( self, button_id, bitmap, short_help, long_help, is_toggle ):
        self.button_id = button_id
        self.bitmap = bitmap
        self.short_help = short_help
        self.long_help = long_help
        self.is_toggle = is_toggle

        if self.long_help is None:
            self.long_help = self.short_help

toolbar_main = ToolBarResource()
toolbar_main.addButton( wb_ids.id_SP_EditCut,
                            'toolbar_images/editcut.png',
                            U_('Cut Files and Folders') )
toolbar_main.addButton( wb_ids.id_SP_EditCopy,
                            'toolbar_images/editcopy.png',
                            U_('Copy Files and Folders') )
toolbar_main.addButton( wb_ids.id_SP_EditPaste,
                            'toolbar_images/editpaste.png',
                            U_('Paste Files and Folders') )
toolbar_main.addButton( wb_ids.id_Command_Shell,
                            'toolbar_images/terminal.png',
                            U_('Command Shell'),
                            U_('Start new command shell') )
toolbar_main.addButton( wb_ids.id_File_Browser,
                            'toolbar_images/file_browser.png',
                            U_('File Browser') )
toolbar_main.addButton( wb_ids.id_File_Edit,
                            'toolbar_images/edit.png',
                            U_('Edit File') )
toolbar_main.addButton( wb_ids.id_Shell_Open,
                            'toolbar_images/open.png',
                            U_('Open File') )
toolbar_main.addButton( wb_ids.id_SP_DiffWorkBase,
                            'toolbar_images/diff.png',
                            U_('Diff changes against base') )
toolbar_main.addButton( wb_ids.id_SP_History,
                            'toolbar_images/history.png',
                            U_('Show History log') )
toolbar_main.addButton( wb_ids.id_SP_Info,
                            'toolbar_images/info.png',
                            U_('File Information') )
toolbar_main.addButton( wb_ids.id_SP_Properties,
                            'toolbar_images/property.png',
                            U_('File Properties') )
toolbar_main.addButton( wb_ids.id_SP_Add,
                            'toolbar_images/add.png',
                            U_('Add Files and Folders') )
toolbar_main.addButton( wb_ids.id_SP_Delete,
                            'toolbar_images/delete.png',
                            U_('Delete selected Files and Folders') )
toolbar_main.addButton( wb_ids.id_SP_Revert,
                            'toolbar_images/revert.png',
                            U_('Revert selected Files and Folders') )
toolbar_main.addButton( wb_ids.id_SP_Lock,
                            'toolbar_images/lock.png',
                            U_('Lock File') )
toolbar_main.addButton( wb_ids.id_SP_Unlock,
                            'toolbar_images/unlock.png',
                            U_('Unlock File') )
toolbar_main.addButton( wb_ids.id_SP_Checkin,
                            'toolbar_images/checkin.png',
                            U_('Checkin changes') )
toolbar_main.addButton( wb_ids.id_SP_Update,
                            'toolbar_images/update.png',
                            U_('Update working copy') )
toolbar_main.addButton( wb_ids.id_View_Recursive,
                            'toolbar_images/flatview.png',
                            U_('Use recursive (flat) view'),
                            is_toggle=True),
toolbar_main.addButton( wb_ids.id_View_OnlyChanges,
                            'toolbar_images/onlychanges.png',
                            U_('Show only changed files'),
                            is_toggle=True),

(toolbar_main.addGroup( 'edit' )
                .addToGroup( wb_ids.id_SP_EditCut )
                .addToGroup( wb_ids.id_SP_EditCopy )
                .addToGroup( wb_ids.id_SP_EditPaste ))
(toolbar_main.addGroup( 'shell' )
                .addToGroup( wb_ids.id_Command_Shell )
                .addToGroup( wb_ids.id_File_Browser ))
(toolbar_main.addGroup( 'file' )
                .addToGroup( wb_ids.id_File_Edit )
                .addToGroup( wb_ids.id_Shell_Open ))
(toolbar_main.addGroup( 'diff' )
                .addToGroup( wb_ids.id_SP_DiffWorkBase )
                .addToGroup( wb_ids.id_SP_History )
                .addToGroup( wb_ids.id_SP_Info )
                .addToGroup( wb_ids.id_SP_Properties ))
(toolbar_main.addGroup( 'add' )
                .addToGroup( wb_ids.id_SP_Add )
                .addToGroup( wb_ids.id_SP_Delete )
                .addToGroup( wb_ids.id_SP_Revert ))
(toolbar_main.addGroup( 'lock' )
                .addToGroup( wb_ids.id_SP_Lock )
                .addToGroup( wb_ids.id_SP_Unlock ))
(toolbar_main.addGroup( 'checkin' )
                .addToGroup( wb_ids.id_SP_Checkin )
                .addToGroup( wb_ids.id_SP_Update ))
(toolbar_main.addGroup( 'view' )
                .addToGroup( wb_ids.id_View_Recursive )
                .addToGroup( wb_ids.id_View_OnlyChanges ))
