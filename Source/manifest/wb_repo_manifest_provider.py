'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_repo_manifest_provider.py

'''

import os
import shutil

import wb_utils
import wb_repo_manifest

import wb_manifest_providers

__version__ = "1.1"

def registerProvider():
    wb_manifest_providers.registerProvider( ManifestProvider( 'manifest' ) )

def joinUri( uri, val ):
    ret = uri
    if val.get( 'checkout' ) != None:
        ret += '/%s' % val['checkout']

    return ret.replace( '//', '/' )

def _catUri( val ):
    return joinUri( val.get( 'uri', '' ), val )

class _Node:
    def __init__( self, attrs, child=None ):
        self.attrs = attrs
        self.childNodes = list()
        if child != None:
            self.childNodes.append( child )

    def getAttribute( self, attr ):
        return self.attrs.get( attr )

class ManifestEditor(wb_manifest_providers.Editor):
    def __init__( self, project_info, **kws ):
        wb_manifest_providers.Editor.__init__( self, project_info, **kws )

        # cache the lined configspec to a list
        if project_info != None:
            self.manifest = wb_repo_manifest.Manifest( project_info.manifest )
        else:
            self.manifest = wb_repo_manifest.Manifest( '' )

    def getManifest( self, **kws ):
        return self.manifest.dump()

class ManifestProvider(wb_manifest_providers.Provider):
    def __init__( self, name ):
        self.inst = None
        wb_manifest_providers.Provider.__init__( self, name )

    def getAboutString( self ):
        return 'Manifest %s' % __version__

    def require( self, project_info, **kws ):
        wb_manifest_providers.Provider.require( self, project_info )

        if project_info != None and ( not hasattr( project_info, 'manifest' ) ):
            return False

        self.inst = wb_repo_manifest.Manifest( project_info.manifest )
        if self.inst.getError() != None:
            return False

        return True

    def getEditor( self ):
        return ManifestEditor( self.project_info )

    def getError( self ):
        if self.inst is None:
            return None
        else:
            return self.inst.getError()

    def __returnElement( self, scipath, element, repom ):
        ret = list()
        repodir = ''

        a = element.get( ( 'name', 'revision', 'path', 'checkout', 'uri') )

        # create the uri for RCS
        uri = a['uri']
        if uri.startswith( self.prefix ):
            uri = uri[ len( self.prefix ): ]
        if uri.endswith( '/' ):
            uri = uri[ :len( uri ) - 1 ]

        # remove leading /vobs/package
        segments = list()
        if uri != None:
            segments = uri.split( '/' )
            if segments[0] == '':
                segments.pop( 0 )
            if segments[0] == self.prefix:
                segments.pop( 0 )

        if repom != None:
            repodir = repom[ segments[0] ]
            segments.pop( 0 )

        revision = a['revision']
        if revision != None:
            revs = revision.split( '/' )
            if len( revs ) > 0 and revs[-1] == 'LATEST':
                revs.pop( -1 )
        else:
            revision = ''

        if revision == '/main/LATEST':
            # trunk
            pa = '%s/trunk' % repodir
            while len( segments ) > 0:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_providers.Rule( scipath,
                            '%s/%s' % ( pa, joinUri( ppath, a ) ) ) )
        elif revision.find( '/' ) > -1:
            # branch
            pa = '%s/branches' % repodir
            while len( segments ) > 0:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_providers.Rule( scipath,
                            '%s/%s' % ( pa, joinUri( ppath, a ) ),
                            remote=pa, checkout=a.get( 'checkout' ) ) )
        else:
            # tags
            tags = list()
            if revision.find( '-' ) > 0:
                tags.append( '%s/tags/%s' % ( repodir, revision ) )
                rev = revision.rsplit( '-', 1 )
                tags.append( '%s/tags/%s/%s' % ( repodir, rev[0], rev[1] ) )
            else:
                # it targets to support to suppress the package name following
                # the rule to build the assumed two uris and the original one
                name = segments[-1]
                if name != None and len( name ) != '':
                    name = name.upper()

                    tags.append( '%s/tags/%s-%s' % ( repodir, name, revision ) )
                    tags.append( '%s/tags/%s/%s' % ( repodir, name, revision ) )
                    tags.append( '%s/tags/%s' % (repodir, revision) )

            # build the path in order
            for t in tags:
                ppath = segments[-1]
                ret.append( wb_manifest_providers.Rule( scipath,
                            '%s/%s' % ( t, joinUri( ppath, a ) ) ) )
            for t in tags:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_providers.Rule( scipath,
                            '%s/%s' % ( t, joinUri( ppath, a ) ) ) )

        return ret

    def getRepoExtras( self, rootdir, repo_map_list=None ):
        listp = list()

        extras = self.inst.match( None )

        for e in extras or list():
            # build up the checked-out directory
            path = e.get( 'path' )
            if path == None:
                path = e.get( 'uri' )
                if path != None:
                    path = path.replace( self.prefix, '' )

            rpath = os.path.join( rootdir, path )
            listp += self.__returnElement( rpath, e, repo_map_list )

        return listp

    def match( self, repo_map_list, rootdir, scipath ):
        listp = list()

        scipath = wb_utils.formatPath( scipath )
        rootdir = wb_utils.formatPath( rootdir )

        rpath = scipath.replace( rootdir, self.prefix )
        rules = self.inst.match( rpath )

        for e in rules or list():
            listp += self.__returnElement( rpath, e, repo_map_list )

        return listp

    def handlePostAction( self, action, **kws ):
        if action == wb_manifest_providers.Provider.ACTION_CHECKOUT \
        or action == wb_manifest_providers.Provider.ACTION_UPDATE:
            elements = list()
            for e in self.inst.elements:
                if e.name == 'copyfile' or e.name == 'mkdir':
                    elements.append( e )

            for e in elements:
                try:
                    if e.name == 'copyfile':
                        src = e.attrs.get( 'src' )
                        dest = e.attrs.get( 'dest' )
                        path = e.parent.attrs.get( 'path' )

                        if src != None and dest != None:
                            srcp = os.path.join( self.project_info.wc_path, path, src )
                            destp = os.path.join( self.project_info.wc_path, dest )

                            shutil.copyfile( srcp, destp )
                    elif e.name == 'mkdir':
                        where = e.attrs.get( 'path' )
                        path = e.parent.attrs.get( 'path' )

                        if where != None:
                            ppath = os.path.join( self.project_info.wc_path, path, where )
                            os.mkdir( ppath )
                except:
                    print 'Error: Wrong with ' + str( e )
