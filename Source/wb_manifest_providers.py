'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_manifest_providers.py

'''

import wb_utils
import wb_exceptions

_manifest_providers = {}

def hasProvider( name ):
    return _manifest_providers.has_key( name )

def getProvider( name ):
    return _manifest_providers[ name ]

def getProviders():
    return _manifest_providers.values()

def registerProvider( provider ):
    _manifest_providers[ provider.name ] = provider

def getProviderAboutStrings():
    about_string = ''
    for provider in _manifest_providers.values():
        about_string += provider.getAboutString() + '\n'

    return about_string

class Rule:
    def __init__( self, localp, remotep, repo=None, revision=None, checkout=None ):
        self.repo = repo
        self.revision = revision
        self.localp = wb_utils.formatPath( localp )
        # the value of 'remotep' could contains starisk as the wildcard
        self.remotep = wb_utils.formatPath( remotep )
        self.checkout = checkout

    def __str__( self ):
        return '<wb_manifest_providers.Rule repo=%s, revision=%s\n' \
               '  localp=%s, remotep=%s, mcheckout=%s' % (
               self.repo, self.revision, self.localp, self.remotep, self.checkout )

class Editor:
    def __init__( self, project_info, **kws ):
        self.project_info = project_info

    def insert( self, pos, context, *args, **kws ):
        return context

    def append( self, context, *args, **kws ):
        return context

    def replace( self, pattern, context, *args, **kws ):
        return context

    def remove( self, pattern, *args, **kws ):
        return ''

    def getManifest( self, **kws ):
        return ''

class Provider:
    def __init__( self, name ):
        self.name = name
        self.prefix = '/vobs'
        self.project_info = None
        self.manifestp = 'subversion'

    def require( self, project_info, **kws ):
        self.project_info = project_info

        # fetch repository configuration
        if hasattr( project_info, 'app' ) \
        and hasattr( project_info.app, 'prefs' ):
            p = project_info.app.prefs.getRepository()
            self.prefix = p.repo_prefix

        return False

    def getEditor( self ):
        return Editor( self.project_info )

    def getError( self ):
        return None

    def getRepositories( self ):
        return None

    # the result are the list with the class 'Rule'
    def getRepoExtras( self, rootdir, mappings=None ):
        return None

    # the result are the list with the class 'Rule'
    def match( self, scipath ):
        raise wb_exceptions.InternalError( 'match not implemented' )

    def getAboutString( self ):
        raise wb_exceptions.InternalError( 'getAboutString not implemented' )

    def getCopyrightString( self ):
        raise wb_exceptions.InternalError( 'getCopyrightString not implemented' )
