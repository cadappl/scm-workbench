'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_manifest_providers.py

'''

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
    for provider in _source_code_providers.values():
        about_string += provider.getAboutString() + '\n'

    return about_string

class Rule:
    def __init__( self, localp, remotp, repo=None, revision=None, mcheckout=None ):
        self.repo = repo
        self.revision = revision
        self.localp = localp
        # the value of 'remotep' could contains starisk as the wildcard
        self.remotp = remotp
        self.mcheckout = mcheckout

class Editor:
    def __init__( self, provider_name, manifest, **kws ):
        self.manifest = manifest
        self.provider_name = provider_name

    def insert( self, pos, context, *args, **kws ):
        return context

    def append( self, context, *args, **kws ):
        return context

    def replace( self, pattern, context, *args, **kws ):
        return context

    def remove( self, pattern, *args, **kws ):
        return ''

    def getValue( self, **kws ):
        return ''

class Provider:
    def __init__( self, name ):
        self.name = name
        self.project_info = None
        self.manifestp = 'subversion'

    def require( self, project_info, **kws ):
        self.project_info = project_info

        # fetch repository configuration
        p = project_info.app.prefs.getRepository()
        self.prefix = p.repo_prefix

        return False

    def getEditor( self ):
        return Editor( self.name, self.project_info )

    def getRepositories( self ):
        raise wb_exceptions.InternalError( 'getRepositories not implemented' )

    # the result are the list with the class 'Rule'
    def match( self, scipath ):
        raise wb_exceptions.InternalError( 'match not implemented' )

    def getAboutString( self ):
        raise wb_exceptions.InternalError( 'getAboutString not implemented' )

    def getCopyrightString( self ):
        raise wb_exceptions.InternalError( 'getCopyrightString not implemented' )
