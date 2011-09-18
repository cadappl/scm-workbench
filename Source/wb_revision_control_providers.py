'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_source_control_providers.py

'''

import wb_exceptions

_revision_providers = {}

def hasProvider( name ):
    return _revision_providers.has_key( name )

def getProvider( name ):
    return _revision_providers[ name ]

def getProviders():
    return _revision_providers.values()

def registerProvider( provider ):
    _revision_providers[ provider.name ] = provider

def getProviderAboutStrings():
    about_string = ''
    for provider in _revision_providers.values():
        about_string += provider.getAboutString() + '\n'

    return about_string

class Provider:
    def __init__( self, name ):
        self.name = name
        self.function = dict()

    def getProjectInfo( self, app, parent ):
        raise wb_exceptions.InternalError( 'getProjectInfo not implemented' )

    def getProjectTreeItem( self, app, project_info ):
        raise wb_exceptions.InternalError( 'getProjectTreeItem not implemented' )

    def getListHandler( self, app, list_panel, project_info ):
        raise wb_exceptions.InternalError( 'getListHandler not implemented' )

    def getAboutString( self ):
        raise wb_exceptions.InternalError( 'getAboutString not implemented' )

    def getCopyrightString( self ):
        raise wb_exceptions.InternalError( 'getCopyrightString not implemented' )

    def getPreferencePanels( self ):
        return list()

    def getProjectDialog( self ):
        return None
