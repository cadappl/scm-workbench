'''
 ====================================================================
 Copyright (c) 2010-2011 ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_configspec_provider.py

'''

import re

import wb_utils
import wb_exceptions

import wb_configspec
import wb_manifest_providers

def registerProvider():
    wb_manifest_providers.registerProvider( ConfigspecProvider( 'configspec' ) )

class ConfigspecEditor(wb_manifest_providers.Editor):
    def __init__( self, project_info, **kws ):
        wb_manifest_providers.Editor.__init__( self, project_info, **kws )

        # cache the lined configspec to a list
        if project_info != None:
            self.cs = wb_configspec.Configspec( project_info.manifest )
        else:
            self.cs = wb_configspec.Configspec( '' )

    def insert( self, ki, pattern, *args, **kws ):
        tp = kws.get( 'format' )

        # find the location to insert
        if ki < 0:
            matches = self.cs.match( pattern )
            if len( matches ) > 0:
                # get the longest match
                e = matches[0]
                for k in range( 1, len( matches ) ):
                    if len( matches[k].get( 'pattern' ) ) > len( e.get( 'pattern' ) ):
                        e = matches[k]

                # generally the inserted line should be ahead of the found one
                slots = self.__findTorunSlots()
                t = self.__belongs( slots, e.lineno )
                if t == -1:
                    ki = 0
                elif t == 0:
                    ki = self.__getlast( slots, t )
                else:
                    ki = self.__getlast( slots, t - 1 )

        if ki > len( self.cs.zparsed ):
            ki = len( self.cs.zparsed )

        if ki < 0 or len( self.cs.zparsed ) == 0:
            ki = 0
            lineno = 0
        elif ki < len( self.cs.zparsed ):
            lineno = self.cs.zparsed[ki].lineno
        else:
            lineno = self.cs.zparsed[ len( self.cs.zparsed ) - 1].lineno + 1

        if pattern == '':
            rule = wb_configspec.EmptyLineRule( lineno, '' )
        elif pattern != None and len( pattern ) > 0 and pattern[0] == '#':
            rule = wb_configspec.CommentRule( lineno, pattern )
        elif tp == 'NOTE':
            if len( pattern ) > 0 and pattern[0] == '=':
                line = '#%s' % pattern
            else:
                line = '# %s' % pattern

            rule = wb_configspec.CommentRule( lineno, line )
        elif ( tp == 'ELEMENT' or tp == None ) and len( args ) > 0:
            line = 'element %s %s' % ( pattern, args[0] )
            rule = wb_configspec.ElementRule( lineno, line )
        else:
            print 'Error: unknown type "%s"' % tp
            return None

        # adjust the lines after the inserting point
        self.cs.zparsed.insert( ki, rule )
        for k, item in enumerate( self.cs.zparsed ):
            if k > ki:
                item.lineno += 1

        return rule

    def append( self, pattern, *args, **kws ):
        return self.insert( 0xfffffffe, pattern, *args, **kws )

    def replace( self, pattern, selector, *args, **kws ):
        if selector is None:
            return self.remove( pattern, *args, **kws )

        count = 0
        for item in self.cs.zparsed:
            if item.match( pattern ):
                item.set( selector )
                count += 1

        return count

    def remove( self, pattern, *args, **kws ):
        # build up the formatted pattern
        pattern = pattern.replace( '\\', '/' )
        if pattern.startswith( '.../' ):
            pattern = pattern[4:]
        if pattern.endswith( '/...' ):
            pattern = pattern[:-4]

        # it removes all lines including modules in packages
        lineno = list()
        for k, item in enumerate( self.cs.zparsed ):
            if item.find( pattern ) > -1:
                lineno.append( k )

        lineno.sort()
        lineno.reverse()

        for no in lineno:
            del self.cs.zparsed[no]

        return len( lineno )

    def getManifest( self, **kws ):
        return self.cs.dump()

    def __replacePrefix( self, file_path ):
        new_path = file_path.replace( self.rootdir, self.prefix ).replace( '\\', '/' )

        return new_path

    def __findTorunSlots( self ):
        # note: the identifier could use sort
        tp = tuple( 'MODULES', 'PACKAGES', 'PROJECT' )

        slots = list( [-1, -1], [-1, -1], [-1, -1] )
        for k, item in enumerate( self.cs.zparsed ):
            if isinstance( item, wb_configspec.CommentRule ):
                m = re.match( '#(.)={3,5}([^=]+)$', item.context )

                if m and tp.index( m[1] ) > -1:
                    id = tp.index( m[1] )
                    if m[0] == '+':
                        slots[id][0] = k
                    else:
                        slots[id][1] = k

        return slots

    def __belongs( self, slots, id ):
        for k, s in enumerate( slots ):
            if s[0] <= id <= s[1]:
                return k

        return -1

    def __getlast( self, slots, k ):
        if 0 <= k < len( slots ):
            return slots[k][1]

        return 0

class ConfigspecProvider(wb_manifest_providers.Provider):
    def __init__( self, name ):
        self.inst = None
        wb_manifest_providers.Provider.__init__( self, name )

    def getAboutString( self ):
        return 'Configspec ' + wb_configspec.__version__

    def require( self, project_info, **kws ):
        # don't support empty manifest for Configspec
        if project_info.manifest != None and len( project_info.manifest ) == 0:
            return False

        wb_manifest_providers.Provider.require( self, project_info )

        if project_info != None and ( not hasattr( project_info, 'manifest' ) ):
            return False

        self.inst = wb_configspec.Configspec( project_info.manifest )
        if self.inst.getError() != None:
            return False

        return True

    def getEditor( self ):
        return ConfigspecEditor( self.project_info )

    def getError( self ):
        if self.inst is None:
            return None
        else:
            return self.inst.getError()

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
        ret = list()

        scipath = wb_utils.formatPath( scipath )
        rootdir = wb_utils.formatPath( rootdir )

        rpath = scipath.replace( rootdir, self.prefix )
        segments = scipath.replace( rootdir, '' ).split( '/' )
        repo = segments[1]

        repodir = repo_map_list.get( repo, '' )
        rules = self.inst.match( rpath )

        # filter out CHECKEDOUT
        filters = dict( {'not-version-selector' : 'CHECKEDOUT'} )
        results = [ r for r in rules or list() if r.filter( filters ) ]

        for r in results or list():
            pattern, selector = r.get( ( 'pattern', 'version-selector' ) )

            patterns = pattern.split( '/' )
            # use a starisk as the wildcard for the selector
            selectors = selector.replace( '...', '*' ).split( '/' )
            # remove the leading /vobs/package
            if patterns[0] == '':
                patterns.pop( 0 )
            if patterns[0] == self.prefix:
                patterns.pop( 0 )
            if patterns[0] == repo:
                patterns.pop( 0 )

            # remove the tailing LATEST
            if selectors[-1] == 'LATEST':
                selectors.pop( -1 )

            # it's not for subversion to support such a method because it's
            # impossible to know where is the start position to split the
            # path to merge the matched parts. The alternative is to add all
            # possible combinations in order, which could invite the
            # mismatch of the target directory.
            #
            # Another solution is to detect the label name in the path,
            # which limits the implementation of subversion. Here, use
            # the first solution.
            #
            # Here it's to use the general solution, and the user should
            # obey the assumption of label.
            if len( selectors ) == 1: # label
                tri_dots = pattern.find( '...' )
                sp = selector.split( '-', 1 )
                label, version = sp[0], '1.0'
                if len(sp) > 1: version = sp[1]

                # refer to VYCdoc30091 to build the two tags
                tags = ( '%s/tags/%s' % ( repodir, selector ),
                       '%s/tags/%s/%s' % ( repodir, label, version ) )

                if tri_dots == pattern.rfind( '...' ) and patterns[-1] == '...':
                    # handle the case "element /vobs/package/pkfoo/... PKFOO-1.0
                    leading = pattern[:tri_dots - 1]
                    lastdir = leading.split( '/' )[-1]
                    extpath = rpath.replace( leading, '' )

                    for t in tags:
                        ret.append( wb_manifest_providers.Rule( scipath,
                                    '%s/%s/%s' % ( t, lastdir, extpath ) ) )
                else:
                    # handle the case that triple dots aren't the tailing ones
                    # add all cases to insert the labels, for instance, the path
                    #  /viewroot/package/foo/bar/foobar and the matched
                    # configspec rule is
                    #  element /vobs/package/.../bar/... ZZZ-1.0
                    #
                    # the build result sets would be:
                    #
                    #  /vobs/tags/ZZZ-1.0/foobar
                    #  /vobs/tags/ZZZ-1.0/bar/foobar
                    #  /vobs/tags/ZZZ-1.0/foo/bar/foobar
                    #
                    pa = '%s/tags/%s' % ( repodir, selector )
                    while len( patterns ) > 0:
                        ppath = '/'.joins( patterns )
                        for t in tags:
                            ret.append( wb_manifest_providers.Rule( scipath,
                                        '%s/%s' % ( t, ppath ) ) )

                        patterns.pop( -1 )
            else:
                if selector == '/main/LATEST':
                    # maps the selector '/main/LATEST' to trunk
                    pa = '%s/trunk' % ( repodir, selector )
                else:
                    # merge the selector with the path
                    pa = '%s/branches' % ( repodir, selector )

                while len( patterns ) > 0:
                    ppath = '/'.join( patterns )
                    ret.append( wb_manifest_providers.Rule( scipath,
                                '%s/%s' % ( pa, ppath ) ) )

                    patterns.pop( -1 )

        return ret
