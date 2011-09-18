'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_repo_manifest.py

'''

__version__ = "1.0"

import xml.dom.minidom

class ManifestElement:
    def __init__( self, name, node, attrs, handle_data=False ):
        self.name = name

        self.data = None
        self.attrs = dict()
        self.nodes = list()

        for attr in attrs or list():
            if isinstance(attr, ( list, tuple ) ):
                attr, _ = attr

            val_attr = node.getAttribute( attr )
            if val_attr != None and len(val_attr) > 0:
                self.attrs[attr] = val_attr

        # the base class doesn't handle the child nodes
        if handle_data and len( node.childNodes ) == 1:
            self.data = node.childNodes[0]

    def dump( self, ident=0 ):
        ret = self.__buildLine( '<%s' % self.name, ident, False )

        for attr in self.attrs:
            ret += ' %s="%s"' % ( attr, self.attrs[attr] )

        if self.data != None:
            ret += '>' + os.linesep
            ret += self.data + os.linesep
            ret += self.__buildLine( '</%s>' % self.name, ident )
        elif len( self.nodes ):
            ret += '>' + os.linesep
            for e in self.nodes:
                ret += e.dump( ident + 1 )
            ret += self.__buildLine( '</%s>' % self.name, ident )
        else:
            ret += self.__buildLine( '/>', 0 )

        return ret

    def get( self, attrs=None ):
        if isinstance( attrs, ( list, tuple ) ):
            ret = list()
            for a in attrs:
                ret.append( self.attrs.get( a ) )

            return ret
        else:
            return self.attrs.get( attrs )

    def match( self, sci_path ):
        return False

    def getRepository( self ):
        return None

    def __buildLine( self, str, ident, eol=True ):
        ret = '  ' * ident + str

        if eol: ret += os.linesep
        return ret

class DefaultElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'default', node,
                                  ( 'remote', 'revision', 'mkbranch' ) )

class RemoteElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'remote', node,
                                  ( 'name', 'fectch', 'review' ) )

class ManifestServerElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'manifest-server', node, ( 'uri' ) )

class NoticeElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'notice', node, None, True )

class ProjectElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'project', node,
            ( 'name', 'remote', 'revision', 'path', 'checkout', 'uri') )

        for n in node.childNodes:
            if n.nodeName == 'copyfile':
                self.nodes.append(
                    ManifestElement( n.nodeName, n, ( 'src', 'dest' ) ) )

    def match( self, sci_path ):
        actual_path = '%s/%s' % ( self.attrs[ 'uri' ], self.attrs[ 'checkout' ] )
        if actual_path.startswith( sci_path ):
            return True

        return False

    def getRepository( self ):
        return self.attrs.get( 'uri' )

class RemoveProjectElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'remove-project', node, ( 'name' ) )

class RepoHooksElement(ManifestElement):
    def __init__(self, node):
        ManifestElement.__init__( self, 'repo-hooks', node,
                                  ( 'in-project', 'enabled-list' ) )

class Manifest:
    def __init__( self, manifest ):
        self.error = None
        self.manifest = manifest

        try:
            self.elements = self.parse( manifest )
        except:
            self.elements = list()
            self.error = 'Error of XML parsing'

    def parse( self, manifest ):
        elem = list()

        root = xml.dom.minidom.parseString( manifest )
        if not root or not root.childNodes:
            self.error = 'Error of root definition'
            return elem

        node = root.childNodes[0]
        if node.nodeName != 'manifest':
            self.error = "Error of root is not manifest"
            return elem

        for n in node.childNodes:
            if n.nodeName == 'default':
                elem.append( DefaultElement( n ) )
            elif n.nodeName == 'remote':
                elem.append( RemoteElement( n ) )
            elif n.nodeName == 'manifest-server':
                elem.append( ManifestServerElement( n ) )
            elif n.nodeName == 'notice':
                elem.append( NoticeElement( n ) )
            elif n.nodeName == 'project':
                elem.append( ProjectElement( n ) )
            elif n.nodeName == 'remove-project':
                elem.append( RemoveProjectElement( n ) )
            elif n.nodeName == 'repo-hooks':
                elem.append( RepoHooksElement( n ) )
            else:
                error = 'Unknown element name: %s' % n.nodeName

        return self.__buildManifest( elem )

    def __buildManifest( self, elements ):
        elem = list()
        # only ProjectManifest can be accepted
        for e in elements:
            if e.name == 'project': elem.push( e )

        for e in elements:
            if e.name == 'remove-project':
                for x in elem[:]:
                    if x.name == e.name:
                        elem.remove( x )

        return elem

    def match( self, scipath ):
        ret = list()

        for e in self.elements:
            if e.match( scipath ):
              ret.append( e )

        return ret

    def getRepositories( self ):
        ret = list()

        for e in self.elements:
            repo = e.getRepository()
            if repo != None and repo not in ret:
                ret.append( repo )

        return ret

    def getError(self):
        return self.error
