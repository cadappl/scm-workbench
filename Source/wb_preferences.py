'''

 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010-2011 SiG Technologies. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_preferences.py

'''
import pprint

import os
import types
import ConfigParser
import UserDict
import copy

import xml.parsers.expat
import xml.dom.minidom
import xml.sax.saxutils

import wx

import wb_platform_specific
import wb_source_control_providers
import wb_toolbars

new_save = True

class ParseError(Exception):
    def __init__( self, value ):
        self.value = value

    def __str__( self ):
        return str(self.value)

    def __repr__( self ):
        return repr(self.value)


class Preferences:
    def __init__( self, app, pref_filename, old_pref_filename ):
        self.app = app
        self.pref_filename = pref_filename
        self.old_pref_filename = old_pref_filename

        self.pref_data = None

        # all the preference section handles get created here
        self.pref_handlers = {}
        self.pref_handlers['Bookmarks'] = BookmarksPreferences( self.app )
        self.pref_handlers['Window'] = WindowPreferences( self.app )
        self.pref_handlers['DiffWindow'] = DiffWindowPreferences( self.app )
        self.pref_handlers['View'] = ViewPreferences( self.app )
        self.pref_handlers['Editor'] = EditorPreferences( self.app )
        self.pref_handlers['Shell'] = ShellPreferences( self.app )
        self.pref_handlers['DiffTool'] = DiffToolPreferences( self.app )
        self.pref_handlers['LogHistory'] = LogHistoryPreferences( self.app )
        self.pref_handlers['Toolbar'] = ToolbarPreferences( self.app )
        self.pref_handlers['Advanced'] = AdvancedPreferences( self.app )
        self.pref_handlers['Repository'] = RepositoryPreferences( self.app )
        self.pref_handlers['RepoBrowser'] = RepoBrowserPreferences( self.app )

        # read preferences into the handlers
        self.readPreferences()

    def loadProjects( self ):
        # separately to handle the project because it's not preferred
        # to limit the usage of the preferences for a project
        self.pref_handlers['Projects'] = ProjectsPreferences( self.app )

        # read preferences into the handlers
        self.readPreferences()

    def readPreferences( self ):
        try:
            self.pref_data = PreferenceData( self.app.log, self.pref_filename, self.old_pref_filename )
        except ParseError, e:
            self.app.log.error( str(e) )
            return

        for handler in self.pref_handlers.values():
            if self.pref_data.has_section( handler.section_name ):
                try:
                    handler.readPreferences( self.pref_data )
                except ConfigParser.Error:
                    self.app.log.error( 'Preferences.readPreferences()', exc_info=1 )

    def __getattr__( self, name ):
        # support getProjects(), getFoobars() etc.
        if name[0:3] == 'get':
            section_name = name[3:]
            if self.pref_handlers.has_key( section_name ):
                return self.pref_handlers[ section_name ]

        raise AttributeError, '%s has no attribute %s' % (self.__class__.__name__, name )


    def writePreferences( self ):
        try:
            for handler in self.pref_handlers.values():
                self.pref_data.remove_section( handler.section_name )
                self.pref_data.add_section( handler.section_name )
                handler.writePreferences( self.pref_data )

            # write the prefs so that a failure to write does not
            # destroy the original
            # also keep one backup copy
            new_name = self.pref_filename + '.tmp'
            old_name = self.pref_filename + '.old'

            f = file( new_name, 'w' )
            self.pref_data.write( f )
            f.close()
            if os.path.exists( self.pref_filename ):
                if os.path.exists( old_name ): # os.rename does not delete automatically on Windows.
                    os.remove( old_name )
                os.rename( self.pref_filename, old_name )
            os.rename( new_name, self.pref_filename )

            self.app.log.info( T_('Wrote preferences to %s') % self.pref_filename )

        except EnvironmentError, e:
            self.app.log.error( 'write preferences: %s' % e )

class PreferenceData:
    def __init__( self, log, xml_pref_filename, ini_pref_filename ):
        self.all_sections = {}

        if os.path.exists( xml_pref_filename ):
            log.info( T_('Reading preferences from %s') % xml_pref_filename )
            self.__readXml( xml_pref_filename )
        else:
            log.info( T_('Reading preferences from %s') % ini_pref_filename )
            self.__readIni( ini_pref_filename )

    def __readXml( self, xml_pref_filename ):
        try:
            f = file( xml_pref_filename, 'r' )
            text = f.read()
            f.close()

            dom = xml.dom.minidom.parseString( text )

        except IOError, e:
            raise ParseError( str(e) )

        except xml.parsers.expat.ExpatError, e:
            raise ParseError( str(e) )

        prefs = dom.getElementsByTagName( 'workbench-preferences' )[0]

        self.__parseXmlChildren( prefs, self.all_sections )

    def __parseXmlChildren( self, parent, data_dict ):
        for child in parent.childNodes:
            if child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:

                if self.__hasChildElements( child ):
                    child_data_dict = {}
                    if child.nodeName in data_dict:
                        if type(data_dict[ child.nodeName ]) != types.ListType:
                            data_dict[ child.nodeName ] = [data_dict[ child.nodeName], child_data_dict]
                        else:
                            data_dict[ child.nodeName ].append( child_data_dict )
                    else:
                        data_dict[ child.nodeName ] = child_data_dict

                    self.__parseXmlChildren( child, child_data_dict )
                else:
                    data_dict[ child.nodeName ] = self.__getText( child )

    def __hasChildElements( self, parent ):
        for child in parent.childNodes:
            if child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
                return True
        return False

    def __getText( self, parent ):
        all_text = []

        for child in parent.childNodes:
            if child.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                all_text.append( child.nodeValue )

        return ''.join( all_text )

    def __readIni( self, pref_filename ):
        pref_data = ConfigParser.RawConfigParser()
        pref_data.read( pref_filename )

        for section_name in pref_data.sections():
            section_dict = {}
            self.all_sections[ section_name ] = section_dict

            for option_name in pref_data.options( section_name ):
                option_name_parts = option_name.split('_')

                if option_name_parts[-1][0] in '0123456789':
                    option_name_prefix = '_'.join( option_name_parts[:-1] )
                    option_name_index = int(option_name_parts[-1])

                    section_dict.setdefault( option_name_index, {} )
                    section_dict[ option_name_index ][ option_name_prefix ]  = pref_data.get( section_name, option_name )
                else:
                    section_dict[ option_name ] = pref_data.get( section_name, option_name )

        for section_name, num_items_name, list_name in [
                    ('Bookmarks','num_bookmarks','bookmark'),
                    ('Projects' ,'num_projects','project')]:
            if self.has_section( section_name ):
                section = self.all_sections[ section_name ]
                section_list = []
                num_items = int( section[ num_items_name ] )
                for index in range( 1, num_items+1 ):
                    section_list.append( section.pop( index ) )
                section[ list_name ] = section_list

    def __getElem( self, element_path ):
        node = self._dom
        for element_name in element_path:
            children = node.childNodes
            node = None
            for child in children:
                if child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE and child.nodeName == element_name:
                    node = child
                    break
            if node is None:
                break

        return node

    def __getAttr( self, element_path, attrib_name ):
        element = self.getElement( element_path )
        if element.hasAttributes() and element.attributes.has_key( attrib_name ):
            return element.attributes[ attrib_name ].value
        return default

    def has_section( self, section_name ):
        return section_name in self.all_sections

    def len_section( self, section_name, option_name ):
        if not self.all_sections[ section_name ].has_key( option_name ):
            return 0
        if type(self.all_sections[ section_name ][ option_name ]) == types.ListType:
            length = len( self.all_sections[ section_name ][ option_name ] )
        else:
            length = 1
        return length

    def has_option( self, section_name, option_name ):
        return option_name in self.all_sections[ section_name ]

    def get( self, section_name, option_name, default='' ):
        return self.all_sections[ section_name ].get( option_name, default )

    def getint( self, section_name, option_name ):
        return int( self.get( section_name, option_name, 0 ).strip() )

    def getfloat( self, section_name, option_name ):
        return float( self.get( section_name, option_name, 0.0 ).strip() )

    def getbool( self, section_name, option_name ):
        return self.get( section_name, option_name, 'false' ).strip().lower() == 'true'

    def remove_section( self, section_name ):
        if section_name in self.all_sections:
            del self.all_sections[ section_name ]

    def add_section( self, section_name ):
        self.all_sections[ section_name ] = {}

    def append_dict( self, section_name, list_name, data ):
        item_list = self.all_sections[ section_name ].setdefault( list_name, [] )
        item_list.append( data )

    def set( self, section_name, option_name, value ):
        self.all_sections[ section_name ][ option_name ] = value

    def write( self, f ):
        f.write( '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' )
        f.write( '<workbench-preferences>\n' )
        self.__writeDictionary( f, self.all_sections, 4 )
        f.write( '</workbench-preferences>\n' )

    def __writeDictionary( self, f, d, indent ):
        all_key_names = d.keys()
        all_key_names.sort()

        for key_name in all_key_names:
            value = d[ key_name ]
            if type(value) == types.DictType:
                if len(value) > 0:
                    f.write( '%*s<%s>\n' % (indent, '', key_name) )
                    self.__writeDictionary( f, value, indent + 4 )
                    f.write( '%*s</%s>\n' % (indent, '', key_name) )
            elif type(value) == types.ListType:
                for item in value:
                    f.write( '%*s<%s>\n' % (indent, '', key_name) )
                    self.__writeDictionary( f, item, indent + 4 )
                    f.write( '%*s</%s>\n' % (indent, '', key_name) )
            else:
                quoted_value = xml.sax.saxutils.escape( unicode( value ) ).encode('utf-8')
                f.write( '%*s<%s>%s</%s>\n' % (indent, '', key_name, quoted_value, key_name) )

class PreferenceSection:
    def __init__( self, section_name ):
        self.section_name = section_name

    def readPreferences( self, pref_data ):
        pass

    def writePreferences( self, pref_data ):
        pass

    # support being returned by the __getattr__ above
    def __call__( self ):
        return self

class GetOption:
    def __init__( self, pref_data, section_name ):
        self.pref_data = pref_data
        self.section_name = section_name

    def has( self, name ):
        return self.pref_data.has_option( self.section_name, name )

    def get( self, name ):
        return self.pref_data.get( self.section_name, name )

    def getstr( self, name ):
        return self.pref_data.get( self.section_name, name ).strip()

    def getint( self, name ):
        return self.pref_data.getint( self.section_name, name )

    def getfloat( self, name ):
        return self.pref_data.getfloat( self.section_name, name )

    def getbool( self, name ):
        return self.pref_data.getbool( self.section_name, name )

    def getstrlist( self, name, sep ):
        s = self.getstr( name )
        if len(s) == 0:
            return []
        return [p.strip() for p in s.split( sep )]

class SetOption:
    def __init__( self, pref_data, section_name ):
        self.pref_data = pref_data
        self.section_name = section_name

    def set( self, name, value, sep='' ):
        #Extend for list saving with a delimiter
        if type(value) == types.ListType and len(sep) > 0:
            value = sep.join( value )

        self.pref_data.set( self.section_name, name, value )

class GetIndexedOption:
    def __init__( self, pref_data, section_name, index, index_name ):
        self.pref_list = pref_data.get( section_name, index_name )
        if type(self.pref_list) != types.ListType:
            self.pref_list = [self.pref_list]

        self.index = index

    def has( self, name ):
        return name in self.pref_list[ self.index ]

    def get( self, name ):
        return self.pref_list[ self.index ][ name ]

    def getstr( self, name ):
        return self.get( name ).strip()

    def getint( self, name ):
        return int( self.getstr( name ) )

    def getfloat( self, name ):
        return float( self.getstr( name ) )

    def getbool( self, name ):
        return self.getstr( name ).lower() == 'true'

class ProjectsPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Projects' )
        self.app = app

        self.all_projects = {}

    def readPreferences( self, pref_data ):
        if not pref_data.has_section( self.section_name ):
            return

        num_projects = pref_data.len_section( self.section_name, 'project' )
        for index in range( num_projects ):
            get_option = GetIndexedOption( pref_data, self.section_name, index, 'project' )
            provider = get_option.getstr( 'provider' )

            if wb_source_control_providers.hasProvider( provider ):
                provider = wb_source_control_providers.getProvider( provider )
                pi = provider.getProjectInfo( self.app )
                pi.readPreferences( get_option )
                self.all_projects[ pi.project_name ] = pi

    def writePreferences( self, pref_data ):
        pref_data.remove_section( self.section_name )
        pref_data.add_section( self.section_name )

        for pi in self.all_projects.values():
            pref_dict = {}

            pi.writePreferences( pref_dict )
            pref_data.append_dict( self.section_name, 'project', pref_dict )

    def _by_project_name( self, a, b ):
        return cmp( a.project_name.lower(), b.project_name.lower() )

    def getProjectList( self ):
        pl = self.all_projects.values()
        pl.sort( self._by_project_name )
        return pl

    def addProject( self, pi ):
        self.all_projects[ pi.project_name ] = pi

    def delProject( self, pi ):
        del self.all_projects[ pi.project_name ]

class BookmarksPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Bookmarks' )
        self.app = app

        self.all_bookmarks = {}
        # no longer support menu style -
        # self.menu_style = 'leaf_only'
        # self.leaf_names_to_ignore = ['main','source','src', 'inc','include']
        self.menu_style = None
        self.leaf_names_to_ignore = []

    def readPreferences( self, pref_data ):
        if not pref_data.has_section( self.section_name ):
            return

        get_option = GetOption( pref_data, self.section_name )
        # look for menu_style and leaf_names_to_ignore to
        # allow for preference file update
        if get_option.has( 'menu_style' ):
            self.menu_style = get_option.getstr( 'menu_style' )

        if get_option.has( 'leaf_names_to_ignore' ):
            self.leaf_names_to_ignore = get_option.getstrlist( 'leaf_names_to_ignore', ',' )

        num_bookmarks = pref_data.len_section( self.section_name, 'bookmark' )
        for index in range( num_bookmarks ):
            get_option = GetIndexedOption( pref_data, self.section_name, index, 'bookmark' )
            bookmark_name = get_option.getstr( 'bookmark_name' )

            provider = get_option.getstr( 'provider' )
            if wb_source_control_providers.hasProvider( provider ):
                provider = wb_source_control_providers.getProvider( provider )
                pi = provider.getProjectInfo( self.app )
                pi.readPreferences( get_option )
                # default the menu name if required
                if pi.menu_name is None:
                    # see if update required
                    if self.menu_style is not None:
                        # default the name as if used to be done
                        pi.menu_name = self.__getMenuName( pi.wc_path )
                    else:
                        self.__defaultMenuName( pi )

                self.all_bookmarks[ bookmark_name ] = pi

    def writePreferences( self, pref_data ):
        pref_data.remove_section( self.section_name )
        pref_data.add_section( self.section_name )

        set_option = SetOption( pref_data, self.section_name )

        all_bookmarks = self.all_bookmarks.items()
        all_bookmarks.sort( key=self.__keyBookmarksMenuAndName )

        for bookmark_name, bookmark in all_bookmarks:
            pref_dict = {}
            pref_dict[ 'bookmark_name' ] = bookmark_name

            bookmark.writePreferences( pref_dict )

            pref_data.append_dict( self.section_name, 'bookmark', pref_dict )

    def __keyBookmarksMenuAndName( self, a_kv ):
        a = a_kv[1]
        k = []
        if a.menu_folder != '':
            k.append( a.menu_folder )

        if a.menu_folder2 != '':
            k.append( a.menu_folder2 )

        if a.menu_folder3 != '':
            k.append( a.menu_folder3 )

        k.append( a.menu_name )

        return k

    def addBookmark( self, pi, name=None ):
        if name is None:
            name = pi.wc_path

        self.all_bookmarks[ name ] = pi
        self.__defaultMenuName( pi )

    def delBookmark( self, bookmark_name ):
        del self.all_bookmarks[ bookmark_name ]

    def delAllBookmarks( self, name ):
        self.all_bookmarks = {}

    def getBookmarkNames( self ):
        names = self.all_bookmarks.keys()
        names.sort()
        return names

    def __defaultMenuName( self, pi ):
        if os.environ.has_key( 'HOME' ):
            home_dir = os.environ[ 'HOME' ] + '/'
            if pi.wc_path.startswith( home_dir ):
                pi.menu_name = pi.wc_path[len(home_dir):]
            else:
                pi.menu_name = pi.wc_path
        else:
            pi.menu_name = pi.wc_path

    # only used to update pref file now
    def __getMenuName( self, wc_path, menu_style=None, leaf_names_to_ignore=None ):
        if menu_style is None:
            menu_style = self.menu_style
        if leaf_names_to_ignore is None:
            leaf_names_to_ignore = self.leaf_names_to_ignore

        if menu_style in ['leaf_in_parent', 'leaf_only']:
            path_parts = wc_path.split( os.path.sep )
            for leaf_index in range( len(path_parts)-1, 1, -1 ):
                if path_parts[ leaf_index ].lower() not in leaf_names_to_ignore:
                    if menu_style == 'leaf_in_parent':
                        return '%s   in %s' % (os.path.sep.join( path_parts[leaf_index:] )
                                              ,os.path.sep.join( path_parts[:leaf_index] ))
                    else:
                        return os.path.sep.join( path_parts[leaf_index:] )

            # cannot reach here?
            return wc_path

        else:
            return wc_path

    def hasBookmark( self, name ):
        return self.all_bookmarks.has_key( name )

    def getBookmark( self, name ):
        return self.all_bookmarks[ name ]


class WindowPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Window' )
        self.app = app

        self.h_sash_ratio = 0.7
        self.v_sash_ratio = 0.2

        self.__frame_size = wx.Size( 700, 500 )
        self.frame_position = wx.DefaultPosition
        self.maximized = False
        self.zoom = 0

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )
        x = get_option.getint( 'pos_x' )
        if x < 0:
            x = 0
        y = get_option.getint( 'pos_y' )
        if y < 0:
            y = 0
        self.frame_position = wx.Point( x, y )

        w = get_option.getint( 'width' )
        h = get_option.getint( 'height' )
        self.__frame_size = wx.Size( w, h )

        self.maximized = get_option.getbool( 'maximized' )
        if get_option.has( 'zoom' ):
            self.zoom = get_option.getint( 'zoom' )
        if get_option.has( 'h_sash_ratio' ):
            self.h_sash_ratio = get_option.getfloat( 'h_sash_ratio' )
        if get_option.has( 'v_sash_ratio' ):
            self.v_sash_ratio = get_option.getfloat( 'v_sash_ratio' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        set_option.set( 'pos_x', self.frame_position.x )
        set_option.set( 'pos_y', self.frame_position.y )
        set_option.set( 'width', self.__frame_size.GetWidth() )
        set_option.set( 'height', self.__frame_size.GetHeight() )
        set_option.set( 'maximized', self.maximized )
        set_option.set( 'zoom', self.zoom )
        set_option.set( 'h_sash_ratio', self.h_sash_ratio )
        set_option.set( 'v_sash_ratio', self.v_sash_ratio )

    def getFrameSize( self ):
        return self.__frame_size

    def setFrameSize( self, size ):
        self.__frame_size = size

class NamedWindowPreferences(PreferenceSection):
    def __init__( self, app, title ):
        PreferenceSection.__init__( self, 'DiffWindow' )
        self.app = app

        self.__frame_size = wx.Size( 700, 500 )
        self.frame_position = wx.DefaultPosition
        self.maximized = False
        self.zoom = 0

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )
        x = get_option.getint( 'pos_x' )
        if x < 0:
            x = 0
        y = get_option.getint( 'pos_y' )
        if y < 0:
            y = 0
        self.frame_position = wx.Point( x, y )

        w = get_option.getint( 'width' )
        h = get_option.getint( 'height' )
        self.__frame_size = wx.Size( w, h )

        self.maximized = get_option.getbool( 'maximized' )
        if get_option.has( 'zoom' ):
            self.zoom = get_option.getint( 'zoom' )


    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        set_option.set( 'pos_x', self.frame_position.x )
        set_option.set( 'pos_y', self.frame_position.y )
        set_option.set( 'width', self.__frame_size.GetWidth() )
        set_option.set( 'height', self.__frame_size.GetHeight() )
        set_option.set( 'maximized', self.maximized )
        set_option.set( 'zoom', self.zoom )

    def getFrameSize( self ):
        return self.__frame_size

    def setFrameSize( self, size ):
        self.__frame_size = size

class DiffWindowPreferences(WindowPreferences):
    def __init( self, app ):
        NamedWindowPreferences.__init__( self, 'DiffWindow' )

class RepoBrowserPreferences(WindowPreferences):
     def __init( self, app ):
        NamedWindowPreferences.__init__( self, 'RepoBrowser' )

class ViewPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'View' )
        self.app = app

        self.auto_refresh = True
        self.sort_order = 1
        self.sort_field = 'Name'
        self.view_ignored = False
        self.view_controlled = True
        self.view_uncontrolled = True
        self.view_recursive = False
        self.view_onlychanges = False
        self.column_order = ['State','Name','Date','Rev','Author','Type']
        self.column_widths = ['4','25','14','4','10','4']

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'auto_refresh' ):
            self.auto_refresh = get_option.getbool( 'auto_refresh' )
        if get_option.has( 'sort_order' ):
            self.sort_order = get_option.getint( 'sort_order' )
        if get_option.has( 'sort_field' ):
            self.sort_field = get_option.getstr( 'sort_field' )
        if get_option.has( 'view_ignored' ):
            self.view_ignored = get_option.getbool( 'view_ignored' )
        if get_option.has( 'view_controlled' ):
            self.view_controlled = get_option.getbool( 'view_controlled' )
        if get_option.has( 'view_uncontrolled' ):
            self.view_uncontrolled = get_option.getbool( 'view_uncontrolled' )
        if get_option.has( 'view_recursive' ):
            self.view_recursive = get_option.getbool( 'view_recursive' )
        if get_option.has( 'view_onlychanges' ):
            self.view_onlychanges = get_option.getbool( 'view_onlychanges' )
        if get_option.has( 'column_order' ):
            self.column_order = get_option.getstrlist( 'column_order', ',' )
        if get_option.has( 'column_widths' ):
            self.column_widths = get_option.getstrlist( 'column_widths', ',' )
        if self.sort_field not in self.column_order:
            self.sort_field = 'Name'

        # always view controlled on startup
        self.view_controlled = True
        # avoid a blank list box on startup
        self.view_onlychanges = False

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        set_option.set( 'auto_refresh', self.auto_refresh )
        set_option.set( 'sort_order', self.sort_order )
        set_option.set( 'sort_field', self.sort_field )
        set_option.set( 'view_ignored', self.view_ignored )
        set_option.set( 'view_controlled', self.view_controlled )
        set_option.set( 'view_uncontrolled', self.view_uncontrolled )
        set_option.set( 'view_recursive', self.view_recursive )
        set_option.set( 'view_onlychanges', self.view_onlychanges )
        set_option.set( 'column_order', self.column_order, ',' )
        set_option.set( 'column_widths', self.column_widths, ',' )


class EditorPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Editor' )
        self.app = app

        self.editor_image = ''
        self.editor_options = ''

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'editor' ):
            self.editor_image = get_option.getstr( 'editor' )
        if get_option.has( 'editor_options' ):
            self.editor_options = get_option.getstr( 'editor_options' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        if self.editor_image:
            set_option.set( 'editor', self.editor_image )
        if self.editor_options:
            set_option.set( 'editor_options', self.editor_options )

class ShellPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Shell' )
        self.app = app

        self.shell_init_command = ''
        self.shell_terminal = ''
        self.shell_file_browser = ''

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'init_command' ):
            self.shell_init_command = get_option.getstr( 'init_command' )
        if get_option.has( 'terminal' ):
            self.shell_terminal = get_option.getstr( 'terminal' )
        if get_option.has( 'file_browser' ):
            self.shell_file_browser = get_option.getstr( 'file_browser' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        if self.shell_init_command:
            set_option.set( 'init_command', self.shell_init_command )
        if self.shell_terminal:
            set_option.set( 'terminal', self.shell_terminal )
        if self.shell_file_browser:
            set_option.set( 'file_browser', self.shell_file_browser )

class DiffToolPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'DiffTool' )
        self.app = app

        self.diff_tool_mode = 'built-in'
        self.gui_diff_tool = ''
        self.shell_diff_tool = ''
        self.gui_diff_tool_options = ''
        self.shell_diff_tool_options = ''

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'diff_tool_mode' ):
            self.diff_tool_mode = get_option.getstr( 'diff_tool_mode' )
        if get_option.has( 'diff_tool' ):
            self.gui_diff_tool = get_option.getstr( 'diff_tool' )
        if get_option.has( 'shell_diff_tool' ):
            self.shell_diff_tool = get_option.getstr( 'shell_diff_tool' )
        if get_option.has( 'diff_tool_options' ):
            self.gui_diff_tool_options = get_option.getstr( 'diff_tool_options' )
        if get_option.has( 'shell_diff_tool_options' ):
            self.shell_diff_tool_options = get_option.getstr( 'shell_diff_tool_options' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        if self.diff_tool_mode != 'built-in':
            set_option.set( 'diff_tool_mode', self.diff_tool_mode )
        if self.gui_diff_tool != '':
            set_option.set( 'diff_tool', self.gui_diff_tool )
        if self.shell_diff_tool != '':
            set_option.set( 'shell_diff_tool', self.shell_diff_tool )
        if self.gui_diff_tool_options != '':
            set_option.set( 'diff_tool_options', self.gui_diff_tool_options )
        if self.shell_diff_tool_options != '':
            set_option.set( 'shell_diff_tool_options', self.shell_diff_tool_options )

class LogHistoryPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'LogHistory' )
        self.app = app

        self.default_mode = 'show_all'
        self.default_limit = 20
        self.default_since_days_interval = 7
        self.default_include_tags = False

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'default_mode' ):
            self.default_mode = get_option.getstr( 'default_mode' )
        if get_option.has( 'default_limit' ):
            self.default_limit = get_option.getint( 'default_limit' )
        if get_option.has( 'default_since_days_interval' ):
            self.default_since_days_interval = get_option.getint( 'default_since_days_interval' )
        if get_option.has( 'default_include_tags' ):
            self.default_include_tags = get_option.getbool( 'default_include_tags' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        set_option.set( 'default_mode', self.default_mode )
        set_option.set( 'default_limit', self.default_limit )
        set_option.set( 'default_since_days_interval', self.default_since_days_interval )
        set_option.set( 'default_include_tags', self.default_include_tags )

class ToolbarPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Toolbar' )
        self.app = app

        self.toolbar_enable = True
        self.horizontal_orientation = True
        self.bitmap_size = 32
        self.group_order = wb_toolbars.toolbar_main.getAllGroupNames()

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'toolbar_enable' ):
            self.toolbar_enable = get_option.getbool( 'toolbar_enable' )
        if get_option.has( 'horizontal_orientation' ):
            self.horizontal_orientation = get_option.getbool( 'horizontal_orientation' )
        if get_option.has( 'bitmap_size' ):
            self.bitmap_size = get_option.getint( 'bitmap_size' )
        if get_option.has( 'group_order' ):
            self.group_order = get_option.getstrlist( 'group_order', ',' )

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )

        set_option.set( 'toolbar_enable', self.toolbar_enable )
        set_option.set( 'horizontal_orientation', self.horizontal_orientation )
        set_option.set( 'bitmap_size', self.bitmap_size )
        set_option.set( 'group_order', self.group_order, ',' )

class AdvancedPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Advanced' )
        self.app = app

        self.arbitrary_tag_branch = False

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'arbitrary_tag_branch' ):
            self.arbitrary_tag_branch = get_option.getbool('arbitrary_tag_branch')

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )
        set_option.set( 'arbitrary_tag_branch', self.arbitrary_tag_branch )

class RepositoryPreferences(PreferenceSection):
    def __init__( self, app ):
        PreferenceSection.__init__( self, 'Repository' )
        self.app = app

        self.repo_prefix = '/vobs/'
        self.repo_baseline = ''
        self.manifest_name = '.configspec'
        self.repo_default_root = None
        self.repo_mark_root = False

        self.repo_tags = 'tags'
        self.repo_trunk = 'trunk'
        self.repo_branches = 'branches'

        # parent -> indicate the parent of a module
        # pattern -> it's a module identifier file
        # component -> all directories for the module
        self.info_module = dict( {
            'parent'    : '.+modules$',
            'pattern'   : '%D/%F.ident',
            'component' : 'config confm incl srce %F.ident'
          } )
        self.info_package = dict( {
            'parent'    : '.+(package|delivery)\d*$|.+output$',
            'pattern'   : '%D/%F.package',
            'component' : 'config confm env incl modules srce %F.package'
          } )
        self.info_project = dict( {
            'parent'    : '.+project\d*$',
            'pattern'   : '%D/%F.project',
            'component' : 'config confm doc env incl input packages output srce %F.project'
          } )

        self.repo_map_list = dict()

    def readPreferences( self, pref_data ):
        get_option = GetOption( pref_data, self.section_name )

        if get_option.has( 'repo_baseline' ):
            self.repo_baseline = get_option.getstr( 'repo_baseline' )

        if get_option.has( 'manifest_name' ):
            self.manifest_name = get_option.getstr( 'manifest_name')

        if get_option.has( 'repo_default_root ' ):
            self.repo_default_root = get_option.getstr( 'repo_default_root' )

        if get_option.has( 'repo_mark_root' ):
            self.repo_mark_root = get_option.getbool( 'repo_mark_root' )

        if get_option.has( 'repo_prefix' ):
            prefix = get_option.getstr( 'repo_prefix' )
            prefix = prefix.replace( '\\', '/' )
            if prefix[-1] != '/':
                prefix += '/'

            self.repo_prefix = prefix

        if get_option.has( 'repo_tags' ):
            self.repo_tags = get_option.get( 'repo_tags' )

        if get_option.has( 'repo_trunk' ):
            self.repo_trunk = get_option.get( 'repo_trunk' )

        if get_option.has(' repo_branches' ):
            self.repo_branches = get_option.get( 'repo_branches' )

        if get_option.has( 'info_module' ):
            self.info_module = get_option.get( 'info_module' )

        if get_option.has( 'info_package' ):
            self.info_package = get_option.get( 'info_package' )

        if get_option.has( 'info_project' ):
            self.info_project = get_option.get( 'info_project' )

        if get_option.has( 'repo_map_list'):
            mp = get_option.get( 'repo_map_list' )
            # avoid mp is a null value
            if isinstance( mp, dict ):
                listp = mp.get( 'repository' )
                for e in listp:
                    o, v = e[ 'name' ], e[ 'url' ]
                    self.repo_map_list[o] = v

    def writePreferences( self, pref_data ):
        set_option = SetOption( pref_data, self.section_name )
        set_option.set( 'repo_prefix', self.repo_prefix )
        set_option.set( 'repo_baseline', self.repo_baseline )
        set_option.set( 'repo_tags', self.repo_tags )
        set_option.set( 'repo_trunk', self.repo_trunk )
        set_option.set( 'repo_branches', self.repo_branches )
        set_option.set( 'repo_default_root', self.repo_default_root )
        set_option.set( 'repo_mark_root', self.repo_mark_root )

        set_option.set( 'manifest_name', self.manifest_name )

        listp = list()
        for o, v in self.repo_map_list.items():
           d = dict()
           d[ 'name ' ] = o
           d[ 'url' ] = v
           listp.append(d)

        set_option.set( 'repo_map_list', dict( { 'repository' : listp } ) )

    def replaceWithRepositoryPath( self, path ):
        if path == None:
            return None

        if path.startswith( self.repo_prefix ):
            segaments = path.replace( self.repo_prefix, '' ).split( '/' )
            if len( segaments ) > 0:
                vob_name = segaments[0]
                if self.repo_map_list.has_key( vob_name ):
                    segaments[0] = self.repo_map_list[vob_name]
                elif self.repo_default_root != None and len(self.repo_default_root) > 0:
                    segaments.insert( 0, self.repo_default_root )

                path = '/'.join(segaments)

        return path

if __name__ == '__main__':
    class FakeApp:
        def __init__( self ):
            self.log = self

        def info( self, message ):
            print 'Info:',message

        def error( self, message ):
            print 'Error:',message

        def getCredentials( self ):
            pass

    import wb_subversion_provider

    # Register all supported source control providers
    wb_subversion_provider.registerProvider()

    p = Preferences( FakeApp(), '/tmp/t.xml', '/tmp/t.ini' )
    pprint.pprint( p.pref_data.all_sections )
    p.writePreferences()
