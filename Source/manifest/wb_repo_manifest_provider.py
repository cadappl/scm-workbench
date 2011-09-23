'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_repo_manifest_provider.py

'''

import wb_utils
import wb_repo_manifest

import wb_manifest_providers

def registerProvider():
    wb_manifest_providers.registerProvider( ManifestProvider( 'manifest' ) )

def __joinUri( uri, val ):
    ret = '%s/%s' % ( uri, val.get( 'checkout', '' ) )

    return ret.replace( '//', '/' )

def __catUri( val ):
    return __joinUri( val.get( 'uri', '' ), val )

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

    def insert( self, ki, pattern, selector, **kws ):
        tp = kws.get( 'format' )

        # find the location to insert
        matches = self.manifest.match( pattern )
        if ki == -1:
            ki = 0

        if tp == 'NOTE':
            node = _Node( dict(), pattern )
            rule = wb_repo_manifest.NoticeElement( node )
        elif tp == 'ELEMENT' or tp == None:
            node = { 'uri' : pattern, 'revision' : selector }
            rule = wb_repo_manifest.ProjectElement( node )
        else:
            print 'Error: unknown type "%s"' % tp
            return None

        # adjust the lines after the inserting point
        self.elements.insert( ki, rule )
        return rule

    def append( self, pattern, selector, **kws ):
        return self.insert( 0xfffffffe, pattern, selector, **kws )

    def replace( self, pattern, selector, **kws ):
        if selector is None:
            return self.remove( pattern, **kws )

        count = 0
        for item in self.manifest.elements:
            if item.match( pattern ):
                item.set( selector )
                count += 1

        return count

    def remove( self, pattern ):
        # build up the formatted pattern
        pattern = pattern.replace( '\\', '/' )
        if pattern.startswith( '.../' ):
            pattern = pattern[4:]
        if pattern.endswith( '/...' ):
            pattern = pattern[:-4]

        # it removes all lines including modules in packages
        ids = list()
        for k, item in enumerate( elements ):
            if item.find( pattern ) > -1:
                ids.append( k )

        ids.sort()
        ids.reverse()

        for no in ids:
            del self.manifest.elements[no]

        return len( ids )

    def getManifest( self, **kws ):
        return self.manifest.dump()

class ManifestProvider(wb_manifest_providers.Provider):
    def __init__( self, name ):
        self.inst = None
        wb_manifest_providers.Provider.__init__( self, name )

    def getAboutString( self ):
        return 'Manifest v1.0'

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

    def __returnElement( self, scipath, element, repom ):
        ret = list()

        a = element.get( ( 'name', 'revision', 'path', 'checkout', 'uri') )

        # create the uri for RCS
        uri = a['uri']
        if uri.startswith( self.prefix ):
            uri = uri[ len( self.prefix ): ]

        # remove leading /vobs/package
        segments = uri.split( '/' )
        if segments[0] == '':
            segments.pop( 0 )
        if segments[0] == self.prefix:
            segments.pop( 0 )

        repodir = repom[ segments[0] ]
        segments.pop( 0 )

        revision = a['revision']
        revs = revision.split( '/' )
        if len( revs ) > 0 and revs[-1] == 'LATEST':
            revs.pop( -1 )

        if revision == '/main/LATEST':
            # trunk
            pa = '%s/trunk' % repodir
            while len( segments ) > 0:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_provider.Rule( scipath,
                            '%s/%s' % ( pa, __joinUri( ppath, a ) ) ) )
        elif a['revision'].index( '/' ) > -1:
            # branch
            pa = '%s/branches' % repodir
            while len( segments ) > 0:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_provider.Rule( scipath,
                            '%s/%s' % ( pa, __joinUri( ppath, a ) ) ) )
        else:
            # tags
            tags = ( '%s/tags/%s' % ( repodir, revision ), )
            if revision.index( '/' ) > 0:
                rev = revision.split( '-', 1 )
                tags.append( '%s/tags/%s/%s' % ( repodir, rev[0], rev[1] ) )

            for t in tags:
                ppath = '/'.join( segments )
                ret.append( wb_manifest_provider.Rule( scipath,
                            '%s/%s' % ( t, __joinUri( ppath, a ) ) ) )

        return ret

    def getRepositories( self ):
        repo = list()
        listp = self.inst.getRepositories()

        prefix = self.prefix + '/'
        prefix_len = len( prefix )
        # filter out all repositories with the prefix
        for p in listp:
            if p.startswith( prefix ):
                li = p[prefix_len:]
                if li.index( '/' ) > 0: li = li[:li.find( '/' )]
                if li not in repo: repo.append( li )

        repo.sort( wb_utils.compare )

        return repo

    def match( self, repo_map_list, rootdir, scipath ):
        listp = list()

        scipath = wb_utils.formatPath( scipath )
        rootdir = wb_utils.formatPath( rootdir )

        rpath = scipath.replace( rootdir, self.prefix )
        rules = self.inst.match( self, rpath )

        for e in rules or list():
            listp += self.__returnElement( rpath, e, repo_map_list )

        return listp
