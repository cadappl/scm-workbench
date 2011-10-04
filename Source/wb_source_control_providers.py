'''
 ====================================================================
 Copyright (c) 2003-2006 Barry A Scott.  All rights reserved.
 Copyright (c) 2010-2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_source_control_providers.py

'''
import wb_exceptions

_source_code_providers = {}

def hasProvider( name ):
    return _source_code_providers.has_key( name )

def getProvider( name ):
    return _source_code_providers[ name ]

def getProviders():
    return _source_code_providers.values()

def registerProvider( provider ):
    _source_code_providers[ provider.name ] = provider

def getProviderAboutStrings():
    about_string = ''
    for provider in _source_code_providers.values():
        about_string += provider.getAboutString()
        about_string += '\n'

    return about_string

class Provider:
    def __init__( self, name ):
        self.name = name

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

class AddProjectState:
    def __init__( self ):
        self.use_existing = 0
        self.wc_path = ''
        self.url_path = ''
        self.project_name = ''
        self.manifest = ''
        self.manifest_provider = ''

class ProjectInfo:
    def __init__( self, app, parent, provider_name ):
        self.app = app
        self.parent = parent
        self.provider_name = provider_name
        self.project_name = None
        self.new_file_template_dir = ''
        self.menu_name = None
        self.menu_info = None
        self.manifest = ''
        self.menu_folder = ''
        self.menu_folder2 = ''
        self.menu_folder3 = ''
        self.use_background_colour = False
        self.background_colour = (255,255,255)

    def __str__( self ):
        return 'app=%r, parent=%r, provider_name=%s, project_name=%s, ' \
               'manifest=%s' % ( self.app, self.parent, self.provider_name,
               self.project_name, self.manifest )

    def init( self, project_name, **kws ):
        self.project_name = project_name

    def isChild( self, pi ):
        # return tree if pi is a child of this pi
        raise wb_exceptions.InternalError( 'isChild not implemented' )

    def setBackgroundColour( self, use, colour ):
        self.use_background_colour = use
        self.background_colour = colour

    def readPreferences( self, get_option ):
        if get_option.has( 'new_file_template_dir' ):
            self.new_file_template_dir = get_option.getstr( 'new_file_template_dir' )

        if get_option.has( 'menu_folder' ):
            self.menu_folder = get_option.getstr( 'menu_folder' )

        if get_option.has( 'menu_folder2' ):
            self.menu_folder2 = get_option.getstr( 'menu_folder2' )

        if get_option.has( 'menu_folder3' ):
            self.menu_folder3 = get_option.getstr( 'menu_folder3' )

        if get_option.has( 'menu_name' ):
            self.menu_name = get_option.getstr( 'menu_name' )

        if get_option.has( 'background_colour_red' ):
            self.background_colour =    (get_option.getint( 'background_colour_red' )
                                        ,get_option.getint( 'background_colour_green' )
                                        ,get_option.getint( 'background_colour_blue' ))
        else:
            self.background_colour = (255,255,255)

        if get_option.has( 'use_background_colour' ):
            self.use_background_colour = get_option.getbool( 'use_background_colour' )
        else:
            self.use_background_colour = False

    def writePreferences( self, pref_dict ):
        pref_dict[ 'provider' ] = self.provider_name
        pref_dict[ 'name' ] = self.project_name

        if self.new_file_template_dir not in [None,'']:
            pref_dict[ 'new_file_template_dir' ] = self.new_file_template_dir

        if self.menu_name is not None:
            pref_dict[ 'menu_name' ] = self.menu_name

        pref_dict[ 'menu_folder' ] = self.menu_folder
        pref_dict[ 'menu_folder2' ] = self.menu_folder2
        pref_dict[ 'menu_folder3' ] = self.menu_folder3

        if self.use_background_colour:
            pref_dict[ 'use_background_colour' ] = self.use_background_colour
            pref_dict[ 'background_colour_red' ] = self.background_colour[0]
            pref_dict[ 'background_colour_green' ] = self.background_colour[1]
            pref_dict[ 'background_colour_blue' ] = self.background_colour[2]

