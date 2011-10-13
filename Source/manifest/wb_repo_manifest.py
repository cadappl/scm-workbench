'''
 ====================================================================
 Copyright (c) 2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_repo_manifest.py

'''

import os
import xml.dom.minidom

class ManifestElement:
    def __init__( self, parent, name, node, attrs=None, handle_data=False ):
        self.name = name
        self.node = node
        self.parent = parent

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

    def __str__( self ):
        return self.dump()

    def dump( self, indent=0 ):
        ret = self.__buildLine( '<%s' % self.name, indent, False )

        for attr in self.attrs:
            ret += ' %s="%s"' % ( attr, self.attrs[attr] )

        if self.data != None:
            ret += '>' + os.linesep
            ret += self.data + os.linesep
            ret += self.__buildLine( '</%s>' % self.name, indent )
        elif len( self.nodes ):
            ret += '>' + os.linesep
            for e in self.nodes:
                ret += e.dump( indent + 1 )
            ret += self.__buildLine( '</%s>' % self.name, indent )
        else:
            ret += self.__buildLine( '/>', 0 )

        return ret

    def get( self, attrs=None ):
        if isinstance( attrs, ( list, tuple ) ):
            ret = dict()
            for a in attrs:
                if self.attrs.has_key( a ):
                    ret[a] = self.attrs[a]
                else:
                    ret[a] = self.parent.default.get( a )

            return ret
        else:
            return self.attrs.get( attrs )

    def match( self, sci_path ):
        return False

    def getRepository( self ):
        return None

    def __buildLine( self, str, indent, eol=True ):
        ret = '  ' * indent + str

        if eol: ret += os.linesep
        return ret

class DefaultElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'default', node,
                                  ( 'remote', 'revision', 'mkbranch' ) )

class RemoteElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'remote', node,
                                  ( 'name', 'fectch', 'review' ) )

class ManifestServerElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'manifest-server', node, ( 'uri' ) )

class NoticeElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'notice', node, None, True )

class ProjectElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'project', node,
            ( 'name', 'remote', 'revision', 'path', 'checkout', 'uri') )

        for n in node.childNodes:
            if n.nodeName == 'copyfile':
                self.nodes.append(
                    ManifestElement( self, n.nodeName, n, ( 'src', 'dest' ) ) )
            elif n.nodeName == 'mkdir':
                self.nodes.append(
                    ManifestElement( self, n.nodeName, n, ( 'path' ) ) )

    def set( revision ):
        self.attrs[ 'revision' ] = revision

    def match( self, sci_path ):
        actual_path = self.attrs['uri']
        if self.attrs.has_key( 'checkout' ):
            actual_path += '/%s' % self.attrs['checkout']

        if actual_path.startswith( sci_path ):
            return True

        return False

    def getRepository( self ):
        return self.attrs.get( 'uri' )

class RemoveProjectElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'remove-project', node, ( 'name' ) )

class RepoHooksElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'repo-hooks', node,
                                  ( 'in-project', 'enabled-list' ) )

class CommentElement(ManifestElement):
    def __init__( self, parent, node ):
        ManifestElement.__init__( self, parent, 'comment', node )

    def dump( self, indent=0 ):
        return ( '  ' * indent ) + self.node.toxml() + os.linesep

class Manifest:
    def __init__( self, manifest ):
        self.error = None
        self.default = None
        self.manifest = manifest

        try:
            self.elements = self.parse( manifest )
        except:
            self.elements = list()
            if self.error == None:
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
            if n.nodeType == node.COMMENT_NODE:
                elem.append( CommentElement( self, n ) )
            elif n.nodeName == 'default':
                self.default = DefaultElement( self, n )
                elem.append( self.default )
            elif n.nodeName == 'remote':
                elem.append( RemoteElement( self, n ) )
            elif n.nodeName == 'manifest-server':
                elem.append( ManifestServerElement( self, n ) )
            elif n.nodeName == 'notice':
                elem.append( NoticeElement( self, n ) )
            elif n.nodeName == 'project':
                elem.append( ProjectElement( self, n ) )
            elif n.nodeName == 'remove-project':
                elem.append( RemoveProjectElement( self, n ) )
            elif n.nodeName == 'repo-hooks':
                elem.append( RepoHooksElement( self, n ) )
            #else:
            #    error = 'Unknown element name: %s' % n.nodeName

        return self.__buildManifest( elem )

    def __buildManifest( self, elements ):
        elem = elements[:]

        for e in elements:
            if e.name == 'remove-project':
                for x in elem[:]:
                    if x.name == e.name:
                        elem.remove( x )

        return elem

    def match( self, scipath ):
        ret = list()

        for e in self.elements:
            if not isinstance( e, ProjectElement ):
                continue

            if scipath == None or e.match( scipath ):
              ret.append( e )

        return ret

    def getRepositories( self ):
        ret = list()

        for e in self.elements:
            repo = e.getRepository()
            if repo != None and repo not in ret:
                ret.append( repo )

        return ret

    def dump( self ):
        ret = '<?xml version="1.0" encoding="UTF-8"?>' + os.linesep + \
              '<manifest>' + os.linesep

        for e in self.elements:
            ret += e.dump(1)

        ret += '</manifest>'
        return ret

    def getError(self):
        return self.error
