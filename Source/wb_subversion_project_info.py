'''
 ====================================================================
 Copyright (c) 2003-2007 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_project_info.py

'''
import sys
import os
import time
import fnmatch
import threading
import types

import pysvn

import wx

import wb_source_control_providers
import wb_subversion_history
import wb_subversion_annotate
import wb_ids
import wb_exceptions
import wb_subversion_tree_handler
import wb_subversion_list_handler
import wb_subversion_utils

_fast_proplist = True

class ErrorWrapper:
    def __init__( self, args ):
        self.args = args

class ProjectInfo(wb_source_control_providers.ProjectInfo):
    def __init__( self, app, parent ):
        wb_source_control_providers.ProjectInfo.__init__( self, app, parent, 'subversion' )
        self.url = None
        self.wc_path = None
        self.client_fg = None
        self.client_bg = None
        self.dir_status = None
        self.all_files_status = []

        self.all_tree_files_status = []
        self.need_checkout = True
        self.need_properties = False
        self.files_properties = {}

        self.tags_url = None
        self.branches_url = None

        self.notification_of_files_in_conflict = 0

    def __repr__( self ):
        return '<svn.ProjectInfo wc_path=%r>' % self.wc_path
        #return '<wb_subversion_provider.ProjectInfo url=%s, wc_path=%s>' % (self.url, self.wc_path)

    def init( self, project_name, **kws):
        wb_source_control_providers.ProjectInfo.init( self, project_name )

        # subversion specific values
        self.url = kws['url']
        self.wc_path = kws['wc_path']

        if kws.has_key( 'client_fg' ):
            self.client_fg = kws['client_fg']
            self.client_bg = kws['client_bg']
        else:
            # need one client/project/thread
            self.client_fg = pysvn.Client()
            self.client_fg.exception_style = 1
            self.client_fg.commit_info_style = 1
            self.client_fg.callback_get_login = wb_exceptions.TryWrapper( self.app.log, self.app.getCredentials )
            self.client_fg.callback_ssl_server_trust_prompt = wb_exceptions.TryWrapper( self.app.log, self.getServerTrust )

            self.client_bg = pysvn.Client()
            self.client_bg.exception_style = 1
            self.client_bg.commit_info_style = 1
            self.client_bg.callback_get_login = CallFunctionOnMainThread( self.app, self.app.getCredentials )
            self.client_bg.callback_ssl_server_trust_prompt = CallFunctionOnMainThread( self.app, self.getServerTrust )

            self.initNotify()

        self.tags_url = kws.get( 'tags_url', '' )
        self.branches_url = kws.get( 'branches_url', '' )

        # default the tags and branches URLs
        url_parts = self.url.split('/')
        if self.tags_url == '' and 'trunk' in url_parts:
            trunk_index = url_parts.index('trunk')
            url_parts[ trunk_index ] = 'tags'
            self.tags_url = '/'.join( url_parts[:trunk_index+1] )

        url_parts = self.url.split('/')
        if self.branches_url == '' and 'trunk' in url_parts:
            trunk_index = url_parts.index('trunk')
            url_parts[ trunk_index ] = 'branches'
            self.branches_url = '/'.join( url_parts[:trunk_index+1] )

    def getTagsUrl( self, rel_url ):
        if self.parent is not None:
            return self.parent.getTagsUrl( rel_url )
        return self.expandedLabelUrl( self.tags_url, rel_url )

    def getBranchesUrl( self, rel_url ):
        if self.parent is not None:
            return self.parent.getBranchesUrl( rel_url )
        return self.expandedLabelUrl( self.branches_url, rel_url )

    def expandedLabelUrl( self, label_url, rel_url ):
        if label_url is '':
            return ''

        label_url_parts = label_url.split('/')
        wild_parts = 0
        while label_url_parts[-1] == '*':
            del label_url_parts[-1]
            wild_parts += 1

        if wild_parts == 0:
            return label_url

        # replace wild_part dirs from the rel_url
        assert( rel_url[0:len(self.url)] == self.url )
        suffix_parts = rel_url[len(self.url)+1:].split('/')
        label_url_parts.extend( suffix_parts[0:wild_parts] )
        return '/'.join( label_url_parts )

    def initNotify( self ):
        self.notification_of_files_in_conflict = 0
        self.client_fg.callback_notify = wb_exceptions.TryWrapper( self.app.log, self.callback_notify )
        self.client_bg.callback_notify = wb_exceptions.TryWrapper( self.app.log, self.callback_notify )

    def callback_notify( self, arg_dict ):
        # must send messages to the foreground thread to do IO or Linux pthreads hangs

        #print 'Notify: %r' % arg_dict

        # nothing to print if no path
        if arg_dict['path'] == '':
            return

        action = arg_dict['action']
        if( action == pysvn.wc_notify_action.commit_postfix_txdelta
        or action == pysvn.wc_notify_action.annotate_revision ):
            self.app.foregroundProcess( self.app.incProgress, () )
            return

        if wb_subversion_utils.version_info.notify_action_has_failed_lock:
            if action in [pysvn.wc_notify_action.failed_lock,
                            pysvn.wc_notify_action.failed_unlock]:
                self.app.log_client_error( ErrorWrapper( arg_dict['error'] ) )
                return

        # see if we want to handle this action
        if wb_subversion_utils.wc_notify_action_map[ arg_dict['action'] ] is None:
            return

        # reject updates for paths that have no change
        if( action == pysvn.wc_notify_action.update_update
        and arg_dict['content_state'] == pysvn.wc_notify_state.unknown
        and arg_dict['prop_state'] == pysvn.wc_notify_state.unknown ):
            return

        if wb_subversion_utils.wc_notify_type_map[ action ] == 'U':
            # count the interesting update event
            self.app.foregroundProcess( self.app.incProgress, () )

        # count the number of files in conflict
        action_letter = wb_subversion_utils.wc_notify_action_map[ action ]
        if( arg_dict['content_state'] == pysvn.wc_notify_state.conflicted
        or arg_dict['prop_state'] == pysvn.wc_notify_state.conflicted ):
            action_letter = 'C'
            self.notification_of_files_in_conflict += 1

        # print anything that gets through the filter
        msg = '%s %s\n' % (action_letter, arg_dict['path'])
        self.app.foregroundProcess( sys.stdout.write, (msg,) )

    def readPreferences( self, get_option ):
        wb_source_control_providers.ProjectInfo.readPreferences( self, get_option )
        
        # load state from a preference file
        name = get_option.getstr( 'name' )
        url = get_option.getstr( 'url' )
        wc_path = get_option.getstr( 'wc_path' )

        if get_option.has( 'tags_url' ):
            tags_url = get_option.getstr( 'tags_url' )
        else:
            tags_url = ''

        if get_option.has( 'branches_url' ):
            branches_url = get_option.getstr( 'branches_url' )
        else:
            branches_url = ''

        # expand any ~/ or ~user/ in the path
        wc_path = os.path.expanduser( wc_path )
        self.init( name, url=url, wc_path=wc_path, tags_url=tags_url, branches_url=branches_url )

    def writePreferences( self, pref_dict ):
        # save state into a preference file
        wb_source_control_providers.ProjectInfo.writePreferences( self, pref_dict )

        pref_dict[ 'url' ] = self.url
        pref_dict[ 'wc_path' ] = self.wc_path
        pref_dict[ 'tags_url' ] = self.tags_url
        pref_dict[ 'branches_url' ] = self.branches_url

    def isEqual( self, pi ):
        return (self.provider_name == pi.provider_name
            and self.wc_path == pi.wc_path)

    def isChild( self, pi ):
        if type(pi) == types.StringType:
            # see if the wc path of the parent is a prefix of the child
            wc_path_dir = self.wc_path + os.path.sep
            return pi[:len(wc_path_dir)] == wc_path_dir

        else:
            # true if pi is a child of this node

            # only look at our pi's
            if self.provider_name != pi.provider_name:
                return False

            # see if the wc path of the parent is a prefix of the child
            wc_path_dir = self.wc_path + os.path.sep
            return pi.wc_path[:len(wc_path_dir)] == wc_path_dir

    def getWorkingDir( self ):
        return self.wc_path

    def getServerTrust( self, trust_data ):
        realm = trust_data['realm']

        info_list = []
        info_list.append( ( T_('Hostname'), trust_data['hostname']) )
        info_list.append( ( T_('Valid From'), trust_data['valid_from']) )
        info_list.append( ( T_('Valid Until'), trust_data['valid_until']) )
        info_list.append( ( T_('Issuer Name'), trust_data['issuer_dname']) )
        info_list.append( ( T_('Finger Print'), trust_data['finger_print']) )

        trust, save = self.app.getServerTrust( realm, info_list, True )
        return trust, trust_data['failures'], save

    def setNeedProperties( self, state ):
        self.need_properties = state

    def updateStatus( self ):
        self.app.log.debug( 'updateStatus() %r' % self )

        self.all_files_status = []
        self.files_properties = {}
        self.dir_status = None

        self.need_checkout = True
        if not os.path.exists( self.wc_path ):
            return

        p = self.app.prefs.getView()
        try:
            entry = self.client_fg.info( self.wc_path )
        except pysvn.ClientError, e:
            # is it the  'is not a working copy' error?
            if e.args[1][0][1] == pysvn.svn_err.wc_not_directory:
                return

            print 'Error: %s' % e.args[0]
            return

        if entry is None:
            self.url = ''
        else:
            self.url = entry.url

        self.all_files_status = self.client_fg.status( self.wc_path, recurse=p.view_recursive, ignore=False )

        self.need_checkout = False

        # sort list
        self.all_files_status.sort( wb_subversion_utils.by_path )
        # remember dir_status before filtering
        if len(self.all_files_status) > 0 and self.all_files_status[0].path == self.wc_path:
            self.dir_status = self.all_files_status[0]
            del self.all_files_status[0]

        # filter show only the files that the user is interested in
        self.all_files_status = self.filterFilenames( self.all_files_status )

        if self.need_properties:
            # see if the depth API is available
            if wb_subversion_utils.version_info.has_depth:
                try:
                    if p.view_recursive:
                        path_properties = self.client_fg.proplist( self.wc_path, depth=pysvn.depth.infinity )
                    else:
                        path_properties = self.client_fg.proplist( self.wc_path, depth=pysvn.depth.immediates )

                    for path, prop_dict in path_properties:
                        self.files_properties[ os.path.abspath( path ) ] = prop_dict

                except pysvn.ClientError, e:
                    pass

            else:
                if _fast_proplist:
                    for status in self.all_files_status:
                        if status.is_versioned:
                            self.files_properties[ os.path.abspath( status.path ) ] = self.__proplist( status.path )
                else:
                    try:
                        name_list = [status.path for status in self.all_files_status if status.is_versioned]
                        path_properties = self.client_fg.proplist( name_list, recurse=False )

                        for path, prop_dict in path_properties:
                            self.files_properties[ os.path.abspath( path ) ] = prop_dict

                    except pysvn.ClientError, e:
                        pass

        if p.view_recursive:
            wc_path_num_parts = len( self.wc_path.split( os.sep ) ) + 1
            self.all_tree_files_status = []
            for file in self.all_files_status:
                if len( file.path.split( os.sep ) ) == wc_path_num_parts:
                    self.all_tree_files_status.append( file )

        else:
            self.all_tree_files_status = self.all_files_status

    def filterFilenames( self, all_files ):
        p = self.app.prefs.getView()
        filtered_all_files = []

        # divide the files into
        # ignored, uncontroller and controlled
        # and see if the user wishes to see them

        for f in all_files:
            if f.text_status == pysvn.wc_status_kind.ignored:
                if p.view_ignored:
                    filtered_all_files.append( f )
            elif f.text_status == pysvn.wc_status_kind.unversioned:
                if p.view_uncontrolled:
                    filtered_all_files.append( f )
            else:
                if p.view_controlled:
                    filtered_all_files.append( f )

        return filtered_all_files
                

    def getProperty( self, filename, propname ):
        d = self.files_properties.get( filename, {} )
        prop = d.get( propname, None )
        return prop

    def getTreeFilesStatus( self ):
        return self.all_tree_files_status

    def getFilesStatus( self ):
        return self.all_files_status

    def getDirStatus( self ):
        return self.dir_status

    def __proplist( self, path ):
        if os.path.isdir( path ):
            prop_file = os.path.join( path, '.svn', 'dir-props' )
            base_prop_file = os.path.join( path, '.svn', 'dir-prop-base' )
        else:
            dirname, basename = os.path.split( path )
            prop_file = os.path.join( dirname, '.svn', 'props', basename + '.svn-work' )
            base_prop_file = os.path.join( dirname, '.svn', 'prop-base', basename + '.svn-base' )

        result = {}
        try:
            f = file( prop_file )
        except EnvironmentError:
            try:
                f = file( base_prop_file )
            except EnvironmentError:
                return result

        while True:
            line = f.readline()
            if line == '':
                break
            if line == 'END\n':
                break
            code, length = line.split()
            body = f.read( int(length)+1 )
            if code == 'K':
                key = body[:-1]
            elif code == 'V':
                result[ key ] = body[:-1]
            else:
                raise ValueError( 'Unparsed line %s' % line )

        f.close()
        return result

#
#    Used to allow a call to function on the background thread
#    to block until the result return on the main thread is available
#
class CallFunctionOnMainThread:
    def __init__( self, app, function ):
        self.app = app
        self.function = function

        self.cv = threading.Condition()
        self.result = None

    def __call__( self, *args ):
        self.app.log.debug( 'CallFunctionOnMainThread.__call__ calling %r' % self.function )
        self.cv.acquire()

        self.app.foregroundProcess( self._onMainThread, args )

        self.cv.wait()
        self.cv.release()

        self.app.log.debug( 'CallFunctionOnMainThread.__call__ returning %r' % self.function )
        return self.result

    def _onMainThread( self, *args ):
        self.app.log.debug( 'CallFunctionOnMainThread._onMainThread calling %r' % self.function )
        try:
            self.result = self.function( *args )
        finally:
            pass

        self.cv.acquire()
        self.cv.notify()
        self.cv.release()

        self.app.log.debug( 'CallFunctionOnMainThread._onMainThread returning %r' % self.function )
