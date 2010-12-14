'''
 ====================================================================
 Copyright (c) 2003-2007 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All right reserved.

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

wc_path_browse_id = wx.NewId()
wc_path_text_ctrl_id = wx.NewId()
url_trunk_path_text_ctrl_id = wx.NewId()
url_tags_path_text_ctrl_id = wx.NewId()

class ProjectDialog(wx.Dialog):
    def __init__( self, app, parent, title ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.app = app
        self.client = pysvn.Client()
        self.client.exception_style = 1

        self.provider_name = 'subversion'
        self.list_background_colour = None

        # get the list of names to use in the validation
        pi_list = self.app.prefs.getProjects().getProjectList()
        self.pi_names = [pi.project_name for pi in pi_list]

        self.g_sizer = wx.GridBagSizer( 5, 20 )

        self.border = wx.StaticBox( self, -1, T_('Project') )
        self.box = wx.StaticBoxSizer( self.border, wx.VERTICAL )
        self.box.Add( self.g_sizer, 0, wx.EXPAND )

        self.name_label = wx.StaticText( self, -1, T_('Project Name:'), style=wx.ALIGN_RIGHT )
        self.name_ctrl = wx.TextCtrl( self, -1, '', size=(400,-1) )

        self.g_sizer.Add( self.name_label, (0,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.name_ctrl,  (0,1), (1,2), wx.EXPAND )

        self.wc_path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse... ") )

        self.wc_path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.wc_path_ctrl = wx.TextCtrl(self, wc_path_text_ctrl_id, '' )

        self.g_sizer.Add( self.wc_path_label,  (1,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.wc_path_ctrl,   (1,1), (1,2), wx.EXPAND )
        self.g_sizer.Add( self.wc_path_browse, (1,3), (1,1)  )

        self.url_trunk_label = wx.StaticText( self, -1, T_('Subversion Trunk URL:'), style=wx.ALIGN_RIGHT )
        self.url_trunk_ctrl = wx.TextCtrl( self, url_trunk_path_text_ctrl_id, '' )

        self.g_sizer.Add( self.url_trunk_label, (2,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.url_trunk_ctrl,  (2,1), (1,2), wx.EXPAND )

        self.url_tags_label = wx.StaticText( self, -1, T_('Subversion Tags URL:'), style=wx.ALIGN_RIGHT )
        self.url_tags_ctrl = wx.TextCtrl( self, url_tags_path_text_ctrl_id, '' )

        self.g_sizer.Add( self.url_tags_label, (3,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.url_tags_ctrl,  (3,1), (1,2), wx.EXPAND )

        self.url_branches_label = wx.StaticText( self, -1, T_('Subversion Branches URL:'), style=wx.ALIGN_RIGHT )
        self.url_branches_ctrl = wx.TextCtrl( self, url_tags_path_text_ctrl_id, '' )

        self.g_sizer.Add( self.url_branches_label, (4,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.url_branches_ctrl,  (4,1), (1,2), wx.EXPAND )

        self.newfile_dir_label = wx.StaticText( self, -1, T_("New File Template Folder: "), style=wx.ALIGN_RIGHT)
        self.newfile_dir_ctrl = wx.TextCtrl( self, -1, '' )
        self.newfile_dir_browse = wx.Button( self, -1, T_(" Browse... ") )

        self.g_sizer.Add( self.newfile_dir_label,  (5,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.newfile_dir_ctrl,   (5,1), (1,2), wx.EXPAND )
        self.g_sizer.Add( self.newfile_dir_browse, (5,3), (1,1) )

        self.list_background_colour_label = wx.StaticText( self, -1, T_("Background Colour: ") , style=wx.ALIGN_RIGHT)
        self.list_background_colour_ctrl = wx.CheckBox( self, -1, T_("Use custom background colour") )
        self.list_background_colour_example = wx.StaticText( self, -1, T_("Example") , style=wx.ALIGN_CENTER )
        self.list_background_colour_picker = wx.Button( self, -1, T_(" Pick Colour... ") )

        self.g_sizer.Add( self.list_background_colour_label,   (6,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.list_background_colour_ctrl,    (6,1), (1,1), wx.EXPAND )
        self.g_sizer.Add( self.list_background_colour_example, (6,2), (1,1), wx.ALIGN_CENTER|wx.EXPAND )
        self.g_sizer.Add( self.list_background_colour_picker,  (6,3), (1,1) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer_buttons.Add( (250, 20), 1, wx.EXPAND)
        self.h_sizer_buttons.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer_buttons.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.box, 0, wx.EXPAND|wx.ALL, 5 )
        self.v_sizer.Add( self.h_sizer_buttons, 0, wx.EXPAND|wx.ALL, 5 )

        self.SetAutoLayout( True )
        self.SetSizer( self.v_sizer )
        self.v_sizer.Fit( self )
        self.Layout()

        self.CentreOnParent()

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )
        wx.EVT_BUTTON( self, wc_path_browse_id, self.OnBrowseWorkingCopyDir )
        wx.EVT_TEXT( self, wc_path_text_ctrl_id, self.updateControls )
        wx.EVT_TEXT( self, url_trunk_path_text_ctrl_id, self.updateControls )
        wx.EVT_TEXT( self, url_tags_path_text_ctrl_id, self.updateControls )
        wx.EVT_BUTTON( self, self.newfile_dir_browse.GetId(), self.OnBrowseNewFileTemplateDir )

        wx.EVT_BUTTON( self, self.list_background_colour_picker.GetId(), self.OnPickColour )
        wx.EVT_CHECKBOX( self, self.list_background_colour_ctrl.GetId(), self.OnUseColourClicked )

        self._update_controls_lock = False

    def updateControls( self, event=None ):
        # on some platforms we will be reentered when SetValue is called
        if self._update_controls_lock:
            return
        self._update_controls_lock = True

        # If the wc_path exists and is a svn wc then disable the url field
        wc_path = os.path.expanduser( self.wc_path_ctrl.GetValue().strip() )

        url = None
        if os.path.exists( wc_path ):
            try:
                info = self.client.info( wc_path )
                url = info.url
            except pysvn.ClientError:
                pass

        if url is None:
            self.url_trunk_ctrl.Enable( True )
        else:
            self.url_trunk_ctrl.Enable( False )
            if len( self.name_ctrl.GetValue() ) == 0:
                self.name_ctrl.SetValue( os.path.basename( wc_path ) )
            self.url_trunk_ctrl.SetValue( url )

        if( url is not None
        and self.url_tags_ctrl.GetValue().strip() == '' ):
            url_parts = url.split('/')
            if 'trunk' in url_parts:
                trunk_index = url_parts.index('trunk')
                url_parts[ trunk_index ] = 'tags'
                self.url_tags_ctrl.SetValue( '/'.join( url_parts[:trunk_index+1] ) )

        if( url is not None
        and self.url_branches_ctrl.GetValue().strip() == '' ):
            url_parts = url.split('/')
            if 'trunk' in url_parts:
                trunk_index = url_parts.index('trunk')
                url_parts[ trunk_index ] = 'branches'
                self.url_branches_ctrl.SetValue( '/'.join( url_parts[:trunk_index+1] ) )

        self._update_controls_lock = False


    def OnOk( self, event ):
        is_url = self.client.is_url

        name = self.name_ctrl.GetValue().strip()
        if name == '':
            wx.MessageBox( T_('Enter a project name'), style=wx.OK|wx.ICON_ERROR );
            return

        if name in self.pi_names:
            wx.MessageBox( T_('Project %s already exist. Choose another name') % name,
                style=wx.OK|wx.ICON_ERROR );
            return

        url = self.url_trunk_ctrl.GetValue().strip()
        if url == '':
            wx.MessageBox( T_('Enter a Subversion trunk URL'), style=wx.OK|wx.ICON_ERROR );
            return

        if not is_url( url ):
            wx.MessageBox( T_('%s is not a valid Subversion trunk URL') % url,
                style=wx.OK|wx.ICON_ERROR );
            return

        url = self.url_tags_ctrl.GetValue().strip()
        if url and not is_url( url ):
            wx.MessageBox( T_('%s is not a valid Subversion tags URL') % url,
                style=wx.OK|wx.ICON_ERROR );
            return

        url = self.url_branches_ctrl.GetValue().strip()
        if url and not is_url( url ):
            wx.MessageBox( T_('%s is not a valid Subversion tags URL') % url,
                style=wx.OK|wx.ICON_ERROR );
            return

        if self.wc_path_ctrl.GetValue().strip() == '':
            wx.MessageBox( T_('Enter a Working copy path'), style=wx.OK|wx.ICON_ERROR );
            return

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

    def OnBrowseWorkingCopyDir( self, event ):
        filename = os.path.expanduser( self.wc_path_ctrl.GetValue() )
        dir_dialog = wx.DirDialog(
            self,
            T_("Select Working Copy directory"),
            filename,
            style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON )

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.wc_path_ctrl.SetValue( dir_dialog.GetPath() )

        dir_dialog.Destroy()

        self.updateControls()

    def OnBrowseNewFileTemplateDir( self, event ):
        filename = self.newfile_dir_ctrl.GetValue()
        if filename == '':
            filename = self.wc_path_ctrl.GetValue()
        filename = os.path.expanduser( filename )

        dir_dialog = wx.DirDialog(
            self,
            T_("Select New File Template directory"),
            filename,
            style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON )

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.newfile_dir_ctrl.SetValue( dir_dialog.GetPath() )

        dir_dialog.Destroy()

        self.updateControls()

    def OnUseColourClicked( self, event ):
        if self.list_background_colour_ctrl.GetValue():
            self.list_background_colour_picker.Enable( True )
        else:
            self.list_background_colour_picker.Enable( False )

    def OnPickColour( self, event ):
        colour_data = wx.ColourData()
        colour_data.SetChooseFull( True )
        colour_data.SetColour( self.list_background_colour )

        dlg = wx.ColourDialog( self, colour_data )

        if dlg.ShowModal() == wx.ID_OK:

            # If the user selected OK, then the dialog's wx.ColourData will
            # contain valid information. Fetch the data ...
            data = dlg.GetColourData()
            self.list_background_colour = data.GetColour().Get()

            # ... then do something with it. The actual colour data will be
            # returned as a three-tuple (r, g, b) in this particular case.

        dlg.Destroy()

        self.list_background_colour_example.SetBackgroundColour( self.list_background_colour )
        self.list_background_colour_example.Refresh( True )

    def getProjectInfo( self ):
        provider = wb_source_control_providers.getProvider( self.provider_name )
        pi = provider.getProjectInfo( self.app )
        pi.new_file_template_dir = self.newfile_dir_ctrl.GetValue().strip()

        pi.init( self.name_ctrl.GetValue().strip(),
            wc_path=os.path.expanduser( self.wc_path_ctrl.GetValue().strip() ),
            menu_info=self.menu_info,
            url=self.url_trunk_ctrl.GetValue().strip(),
            tags_url=self.url_tags_ctrl.GetValue().strip(),
            branches_url=self.url_branches_ctrl.GetValue().strip() )

        pi.setBackgroundColour( self.list_background_colour_ctrl.GetValue(), self.list_background_colour )

        return pi

class UpdateProjectDialog(ProjectDialog):
    def __init__( self, app, parent, project_info ):
        ProjectDialog.__init__( self, app, parent, T_('Project Settings') )

        self.project_info = project_info

        del self.pi_names[ self.pi_names.index( self.project_info.project_name ) ]

        self.name_ctrl.SetValue( self.project_info.project_name )
        self.url_trunk_ctrl.SetValue( self.project_info.url )
        self.wc_path_ctrl.SetValue( self.project_info.wc_path )
        self.url_tags_ctrl.SetValue( self.project_info.tags_url )
        self.newfile_dir_ctrl.SetValue( self.project_info.new_file_template_dir )

        if self.project_info.use_background_colour:
            self.list_background_colour = self.project_info.background_colour
        else:
            self.list_background_colour = (255,255,255)

        self.list_background_colour_ctrl.SetValue( self.project_info.use_background_colour )
        self.list_background_colour_example.SetBackgroundColour( self.list_background_colour )
        self.list_background_colour_picker.Enable( self.project_info.use_background_colour )

        self.updateControls()

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

        if not self.menu_info:
            self.menu_info = kws.get( 'menu_info', None )

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
