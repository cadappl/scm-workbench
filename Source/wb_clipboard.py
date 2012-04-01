'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_clipboard.py

'''
class Clipboard:
    def __init__( self, all_filenames, is_copy ):
        self.__is_copy = is_copy
        self.__all_filenames = all_filenames

    def isCopy( self ):
        return self.__is_copy

    def isCut( self ):
        return not self.__is_copy

    def getAllFilenames( self ):
        return self.__all_filenames
