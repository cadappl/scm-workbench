'''
 ====================================================================
 Copyright (c) 2010 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_project_info.py

'''

import os
import re
import sys
import wx
import types
import threading
import pysvn

import wb_ids
import wb_read_file
import wb_exceptions
import wb_subversion_utils

import wb_config

import wb_source_control_providers
import wb_subversion_tree_handler
import wb_subversion_list_handler
import wb_subversion_project_info

import wb_torun_configspec

wc_path_browse_id = wx.NewId()
wc_path_text_ctrl_id = wx.NewId()
name_text_ctrl_id = wx.NewId()

class ProjectState:
    def __init__( self ):
        self.name = ''
        self.wc_path = ''
        self.color = ''
        self.configspec = ''
        self.background_colour = 0
        self.use_background_colour = False
        self.new_file_template_dir = ''

class ProjectDialog(wx.Dialog):
    def __init__( self, app, parent, project_info, title ):
        wx.Dialog.__init__( self, parent, -1, title, size=(400,400) )
        self.app = app
        self.v_sizer = None
        self.project_info = project_info

        self.state = ProjectState()
        # get the list of names to use in the validation
        pi_list = self.app.prefs.getProjects().getProjectList()
        self.pi_names = [pi.project_name for pi in pi_list]
        del self.pi_names[ self.pi_names.index( self.project_info.project_name ) ]

        # useful for debugging new pages
        try:
            self.initControls()
        except:
            app.log.exception( T_('ProjectDialog') )

        self.SetSizer( self.v_sizer )
        self.Layout()
        self.Fit()

        self.CentreOnParent()

    def initControls( self ):
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.notebook = wx.Notebook( self )

        self.v_sizer.Add( self.notebook, 0, wx.EXPAND|wx.ALL, 5 )

        self.pages = []
        self.pages.append( ProjectPanel( self, self.notebook, self.app, self.project_info ) )
        self.pages.append( ConfigspecPanel( self, self.notebook, self.app, self.project_info ) )
        self.pages.append( RepositoryPanel( self, self.notebook, self.app, self.project_info ) )

        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( (1, 1), 1, wx.EXPAND )
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def getProjectInfo( self ):
        provider = wb_source_control_providers.getProvider( 'torun' )

        pi = provider.getProjectInfo( self.app )
        pi.new_file_template_dir = self.state.new_file_template_dir
        pi.setBackgroundColour( self.state.use_background_colour, self.state.background_colour )

        pi.init( self.state.name,
            configspec=self.state.configspec,
            wc_path=os.path.expanduser( self.state.wc_path ) )


        return pi

    def updateControls( self ):
        for page in self.pages:
            page.updateControls()

    def OnOk( self, event ):
        for page in self.pages:
            if not page.validate(self.state):
                return

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )

class PagePanel(wx.Panel):
    def __init__( self, notebook, title ):
        wx.Panel.__init__( self, notebook, -1, style = wx.NO_BORDER )

        self.page_v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.page_v_sizer.Add( self.initControls(), 0, wx.EXPAND|wx.ALL, 5 )
        self.SetSizer( self.page_v_sizer )
        self.SetAutoLayout( True )
        self.page_v_sizer.Fit( self )
        self.Layout()

        notebook.AddPage( self, title )

    def initControls( self ):
        raise wb_exceptions.InternalError('must override initControls')

    def validate( self, state ):
        return True

class ProjectPanel(PagePanel):
    def __init__( self, parent, notebook, app, project_info ):
        self.app = app
        self.parent = parent
        self.project_info = project_info

        PagePanel.__init__( self, notebook, T_('Project') )

    def initControls( self ):
        self.list_background_colour = None

        self.g_sizer = wx.GridBagSizer( 5, 20 )

        self.name_label = wx.StaticText( self, -1, T_('Project Name:'), style=wx.ALIGN_RIGHT )
        self.name_ctrl = wx.TextCtrl( self, -1, '', size=(400,-1) )

        self.g_sizer.Add( self.name_label, (0,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.name_ctrl,  (0,1), (1,2), wx.EXPAND )

        self.wc_path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse... ") )

        self.wc_path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.wc_path_ctrl = wx.TextCtrl(self, -1, '' )

        self.g_sizer.Add( self.wc_path_label,  (1,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.wc_path_ctrl,   (1,1), (1,2), wx.EXPAND )
        self.g_sizer.Add( self.wc_path_browse, (1,3), (1,1)  )

        self.newfile_dir_label = wx.StaticText( self, -1, T_("New File Template Folder: "), style=wx.ALIGN_RIGHT)
        self.newfile_dir_ctrl = wx.TextCtrl( self, -1, '' )
        self.newfile_dir_browse = wx.Button( self, -1, T_(" Browse... ") )

        self.g_sizer.Add( self.newfile_dir_label,  (2,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.newfile_dir_ctrl,   (2,1), (1,2), wx.EXPAND )
        self.g_sizer.Add( self.newfile_dir_browse, (2,3), (1,1) )


        self.list_background_colour_label = wx.StaticText( self, -1, T_("Background Colour: ") , style=wx.ALIGN_RIGHT)
        self.list_background_colour_ctrl = wx.CheckBox( self, -1, T_("Use custom background colour") )
        self.list_background_colour_example = wx.StaticText( self, -1, T_("Example") , style=wx.ALIGN_CENTER )
        self.list_background_colour_picker = wx.Button( self, -1, T_(" Pick Colour... ") )

        self.g_sizer.Add( self.list_background_colour_label,   (3,0), (1,1), wx.ALIGN_RIGHT )
        self.g_sizer.Add( self.list_background_colour_ctrl,    (3,1), (1,1), wx.EXPAND )
        self.g_sizer.Add( self.list_background_colour_example, (3,2), (1,1), wx.ALIGN_CENTER|wx.EXPAND )
        self.g_sizer.Add( self.list_background_colour_picker,  (3,3), (1,1) )

        wx.EVT_BUTTON( self, wc_path_browse_id, self.OnBrowseWorkingCopyDir )
        wx.EVT_TEXT( self, wc_path_text_ctrl_id, self.updateControls )
        wx.EVT_BUTTON( self, self.newfile_dir_browse.GetId(), self.OnBrowseNewFileTemplateDir )

        wx.EVT_BUTTON( self, self.list_background_colour_picker.GetId(), self.OnPickColour )
        wx.EVT_CHECKBOX( self, self.list_background_colour_ctrl.GetId(), self.OnUseColourClicked )

        return self.g_sizer

    def updateControls( self ):
        self.name_ctrl.SetValue( self.project_info.project_name )
        self.wc_path_ctrl.SetValue( self.project_info.wc_path )
        self.newfile_dir_ctrl.SetValue( self.project_info.new_file_template_dir )
        if self.project_info.use_background_colour:
            self.list_background_colour = self.project_info.background_colour
        else:
            self.list_background_colour = (255,255,255)

        self.list_background_colour_ctrl.SetValue( self.project_info.use_background_colour )
        self.list_background_colour_example.SetBackgroundColour( self.list_background_colour )
        self.list_background_colour_picker.Enable( self.project_info.use_background_colour )

    def validate( self, state ):
        name = self.name_ctrl.GetValue().strip()
        if name == '':
            wx.MessageBox( T_('Enter a project name'), style=wx.OK|wx.ICON_ERROR );
            return False
        if name in self.parent.pi_names:
            wx.MessageBox( T_('Project %s already exist. Choose another name') % name,
                style=wx.OK|wx.ICON_ERROR );
            return False

        state.name = name
        if self.wc_path_ctrl.GetValue().strip() == '':
            wx.MessageBox( T_('Enter a Working copy path'), style=wx.OK|wx.ICON_ERROR );
            return False

        state.wc_path = self.wc_path_ctrl.GetValue().strip()
        state.use_background_colour = self.list_background_colour_ctrl.GetValue()
        state.background_colour = self.list_background_colour;
        state.new_file_template_dir = self.newfile_dir_ctrl.GetValue().strip()

        return True

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

class ConfigspecPanel(PagePanel):
    def __init__( self, parent, notebook, app, project_info ):
        self.app = app
        self.project_info = project_info

        PagePanel.__init__( self, notebook, T_('Configspec') )

    def initControls( self ):
        self.list_background_colour = None

        self.sizer = wx.BoxSizer( wx.VERTICAL )

        self.configspec_ctrl = wx.TextCtrl( self, -1, size=(-1, 200), style=wx.HSCROLL|wx.TE_MULTILINE|wx.TE_RICH2 )
        self.configspec_ctrl.SetFont(wx.Font(wb_config.point_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, wb_config.face))
        self.sizer.Add( self.configspec_ctrl, 1, wx.EXPAND|wx.ALL )
        self.configspec_edit = wx.Button( self, -1, T_(" Edit... ") )

        wx.EVT_BUTTON( self, self.configspec_edit.GetId(), self.OnEditConfigspec )
        self.sizer.Add( self.configspec_edit, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

        return self.sizer

    def updateControls( self ):
        self.configspec_ctrl.SetValue( self.project_info.configspec )

    def validate( self, state ):
        if self.configspec_ctrl.GetValue().strip() == '':
            wx.MessageBox( T_('Enter a configspec'), style=wx.OK|wx.ICON_ERROR );
            return False

        state.configspec = self.configspec_ctrl.GetValue().strip()
        return True

    def OnEditConfigspec( self, event ):
        pass

class RepositoryPanel(PagePanel):
    def __init__( self, parent, notebook, app, project_info ):
        self.app = app
        self.project_info = project_info

        PagePanel.__init__( self, notebook, T_('Repositories') )

    def initControls( self ):
        self.list_background_colour = None

        repo_names = self.project_info.svn_project_infos.keys()
        repo_map_list = self.app.prefs.getRepository().repo_map_list

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        self.list_box =  wx.ListCtrl( self, -1, wx.DefaultPosition,
                (-1, 225), wx.LC_REPORT )
        self.list_box.InsertColumn( 0, T_('Name') )
        self.list_box.SetColumnWidth( 0, 100 )

        self.list_box.InsertColumn( 1, T_('Location') )
        self.list_box.SetColumnWidth( 1, 400 )

        repo_names.sort(wb_subversion_utils.compare)
        for item in repo_names:
            index = self.list_box.GetItemCount()
            self.list_box.InsertStringItem( index, item )
            self.list_box.SetStringItem( index, 1, repo_map_list[item] )

        self.sizer.Add(self.list_box, 1, wx.EXPAND|wx.ALL)
        return self.sizer

    def updateControls( self ):
        pass

class UpdateProjectDialog(ProjectDialog):
    def __init__( self, app, parent, project_info ):
        ProjectDialog.__init__( self, app, parent, project_info, T_('Project Settings') )
        self.updateControls()
####
# wrap the client_bg to insert the function for update and checkout
#
class SubversionClient:
    def __init__( self, app, project_info ):
        self.app = app
        self.project_info = project_info

        self.client = pysvn.Client()
        self.client.exception_style = 1
#        self.client.commit_info_style = 1
        self.client.callback_get_login = wb_exceptions.TryWrapper( self.app.log, self.app.getCredentials )
        self.client.callback_ssl_server_trust_prompt = wb_exceptions.TryWrapper( self.app.log, self.getServerTrust )

        self.initNotify()

    def initNotify( self ):
        self.client.callback_notify = wb_exceptions.TryWrapper( self.app.log, self.callback_notify )

    def __getattribute__(self, attr):
        print attr

    def info(self, path, **args):
        return self.client.info(path, **args)

    def info2(self, path, **args):
        return self.client.info2(path, **args)

    def status(self, path, **args):
        return self.client.status(path, **args)

    def checkout(self, *arg, **args):
        self.updateWithConfigspec()

        # should update the repository info
        self.project_info.initRepositoryInfo()

    def update(self, *arg, **args):
        self.updateWithConfigspec(False)

    def updateWithConfigspec(self, checkout=True):
        repo_map_list = self.app.prefs.getRepository().repo_map_list
        # handle the configspec, checkout or update the project
        cs_parser = wb_torun_configspec.wb_subversion_configspec(
                        rootdir=self.project_info.wc_path,
                        configspec=self.project_info.configspec)
        # it's assumed the stored configspec is always correct
        dirs = list()
        # 1. find and check out all repositories
        repos = cs_parser.getRepositories()
#        print 'repo=>', repos
        for repo in repos:
            # FIXME: ignore the unmapped repository?
            if not repo_map_list.has_key( repo ): continue
            url = '%s/trunk' % repo_map_list[repo]
            wc_path = '%s/%s' % ( self.project_info.wc_path, repo )
            # build up the repository location with /trunk
            if not os.path.exists( wc_path ):
                self.client.checkout( url, wc_path, depth=pysvn.depth.infinity,
                                      revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            dirs.append( wc_path )

        # 2. update or switch directory according to the configspec
        while len( dirs ) > 0:
#            print '-------------------------------------'
            wc_path = dirs.pop( 0 )
#            print 'wc_path=%s' % wc_path
            # 2.1 get the URL from the path
            url = self.get_url_from_path( wc_path )
            # 2.2 get the target URL from the configspec
            mlist = cs_parser.match( repo_map_list, wc_path )
#            print 'url=>', url
#            print 'mlist=>', mlist
            for new_url in mlist or list():
                if not self.exists( new_url ): continue
                if url == new_url:
                    self.client.update( wc_path, depth=pysvn.depth.empty,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                else:                
                    self.client.switch( wc_path, new_url, depth=pysvn.depth.infinity,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                break

            # cache the directories in current directory
            for d in os.listdir( wc_path ):
                path = os.path.join( wc_path, d )
                if ( not d.startswith( '.' ) ) and os.path.isdir( path ):
                    dirs.append( path )

    def exists( self, filename ):
        dirs = list()
        try:
            dirs = self.client.ls( filename,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )
        except:
            pass

        if len(dirs):
            return True
        else:
            return False

    def get_url_from_path( self, filename ):
        info = self.client.info2( filename, recurse=False )[0][1]

        return info.URL

#FIXME...
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

# Torun is designed to contains multiple subversion projects. The class
# wb_torun_project_info.ProjectInfo isn't inherited from
# wb_subversion_project_info.ProjectInfo but assigned each for a sub-repository
class ProjectInfo(wb_source_control_providers.ProjectInfo):
    def __init__( self, app, parent ):
        wb_source_control_providers.ProjectInfo.__init__( self, app, parent, 'torun' )
        self.url = None
        self.wc_path = None
        self.configspec = ''
        self.app = app
        self.parent = self.parent
        #TODO: check the usage of need_checkout
        self.need_checkout = True
        self.need_properties = False
        self.svn_project_infos = dict()

    def __repr__( self ):
        return '<torun.ProjectInfo wc_path=%r>' % self.wc_path

    def init( self, project_name, **kws):
        wb_source_control_providers.ProjectInfo.init( self, project_name )

        self.wc_path = kws['wc_path']
        self.configspec = kws.get( 'configspec', '' )

        # need one client/project/thread
        self.client_bg = SubversionClient( self.app, self )
        self.client_fg = SubversionClient( self.app, self )

        self.initRepositoryInfo()

    def initRepositoryInfo( self ):
        # build up the subversion project infos
        cs_parser = wb_torun_configspec.wb_subversion_configspec(
                        rootdir=self.wc_path,
                        configspec=self.configspec )

        for repo in cs_parser.getRepositories() or list():
            self.svn_project_infos[repo] = None

        try:
            for repo in self.svn_project_infos.keys():
                wc_path = '%s/%s' % ( self.wc_path, repo )
                url = self.client_bg.get_url_from_path( wc_path )
                # create a temporary subversion project_name '@@repo'
                self.svn_project_infos[repo] = wb_subversion_project_info.ProjectInfo( self.app, self.parent )
                self.svn_project_infos[repo].init('@@%s' % repo, url=url, wc_path=wc_path )
            self.need_checkout = False
        except:
            self.need_checkout = True

    def initNotify( self ):
        self.notification_of_files_in_conflict = 0

        self.client_bg.initNotify()
        self.client_fg.initNotify()

    def readPreferences( self, get_option ):
        wb_source_control_providers.ProjectInfo.readPreferences( self, get_option )

        # load state from a preference file
        name = get_option.getstr( 'name' )
        wc_path = get_option.getstr( 'wc_path' )

        if get_option.has( 'configspec' ):
            configspec = get_option.getstr( 'configspec' )
        else:
            configspec = ''

        # expand any ~/ or ~user/ in the path
        wc_path = os.path.expanduser( wc_path )
        self.init( name, wc_path=wc_path, configspec=configspec )

    def writePreferences( self, pref_dict ):
        # save state into a preference file
        wb_source_control_providers.ProjectInfo.writePreferences( self, pref_dict )

        pref_dict[ 'wc_path' ] = self.wc_path
        if len( self.configspec ):
            pref_dict[ 'configspec' ] = self.configspec

        if len(self.configspec):
            # FIXME: read out configspec name from somewhere
            wb_read_file.writeFileByLine( "%s/.configspec" % self.wc_path, self.configspec )

    def isEqual( self, pi ):
        return (self.provider_name == pi.provider_name
            and self.wc_path == pi.wc_path)

    def isChild( self, pi ):
        # only the subdirectories would be judged as the children
        if type(pi) == types.StringType:
            # see if the wc path of the parent is a prefix of the child
            url = self.url + os.path.sep
            return pi[:len(wc_path)] == wc_path \
              and pi[len(wc_path):].replace( '\\', '/' ).find( '/' ) == -1
        else:
            # true if pi is a child of this node

            # see if the wc path of the parent is a prefix of the child
            wc_path = self.wc_path + os.path.sep

            return pi.wc_path[:len(wc_path)] == wc_path \
              and pi.wc_path[len(wc_path):].replace( '\\', '/' ).find( '/' ) == -1

    def getWorkingDir( self ):
        return self.wc_path

    def mayExpand( self ):
        return len(self.svn_project_infos.keys()) > 0

#FIXME: the interface?
    def updateStatus( self ):
        for repo in self.svn_project_infos:
            if self.svn_project_infos[ repo ]:
                self.svn_project_infos[ repo ].updateStatus()

    def setNeedProperties( self, need_properties ):
        self.need_properties = need_properties

    def getFilesStatus( self ):
        all_files_status = list()
        for repo in self.svn_project_infos:
            if self.svn_project_infos[ repo ]:
                file_status = self.svn_project_infos[ repo ].getDirStatus()
                if file_status:
                    all_files_status.append( file_status )

#        print 'getFilesStatus', all_files_status
        if len(all_files_status):
            return all_files_status
        else:
            return None

    def getTreeFilesStatus( self ):
        all_tree_files_status = list()

        for repo in self.svn_project_infos:
            if self.svn_project_infos[ repo ]:
                tree_files_status = self.svn_project_infos[ repo ].getDirStatus()
                if tree_files_status:
                    all_tree_files_status.append( tree_files_status )

#        print 'getTreeFilesStatus', all_tree_files_status
        return all_tree_files_status

    def getDirStatus( self ):
        all_dir_status = None

        # FIXME: check the function
        for repo in self.svn_project_infos:
            if self.svn_project_infos[ repo ]:
                dir_status = self.svn_project_infos[ repo ].getDirStatus()
                # it just needs one status
                if dir_status and len(dir_status) > 0:
                    all_dir_status = dir_status
                    break

        return all_dir_status

class TorunProject(wb_subversion_tree_handler.SubversionProject):
    def __init__( self, app, project_info ):
        self.project_info = project_info
        wb_subversion_tree_handler.SubversionProject.__init__( self, app, project_info )

    def getContextMenu( self, state ):
        menu_item =[('', wb_ids.id_Command_Shell, T_('&Command Shell') )
            ,('', wb_ids.id_File_Browser, T_('&File Browser') )
            ,('-', 0, 0 )]

        if self.project_info.need_checkout:
            menu_item += [('', wb_ids.id_SP_Checkout, T_('Checkout') )]
        else:
            menu_item += [('', wb_ids.id_SP_Update, T_('Update') )]

        return wb_subversion_utils.populateMenu( wx.Menu(), menu_item )

    def getExpansion( self ):
        project_info_list = []

        for file in self.project_info.getTreeFilesStatus():
            if( (file.entry is None and os.path.isdir( file.path ))
            or (file.entry is not None and file.entry.kind == pysvn.node_kind.dir) ):
                pi = wb_subversion_project_info.ProjectInfo( self.app, self.project_info )
                name = os.path.basename( file.path )
                if file.entry is None or file.entry.url is None:
                    url = '%s/%s' % (self.project_info.url, name )
                else:
                    url = file.entry.url

                # use default subversion clients instead of the ones in ProjectInfo for Torun
                pi.init( name, url=url, wc_path=file.path)
                project_info_list.append( pi )

        return project_info_list

    def getTreeNodeColour( self ):
        if self.project_info.need_checkout:
            return wb_config.colour_status_need_checkout
        else:
            return wb_config.colour_status_normal

class TorunListHandler(wb_subversion_list_handler.SubversionListHandler):
    def __init__( self, app, list_panel, project_info ):
        wb_subversion_list_handler.SubversionListHandler.__init__( self, app, list_panel, project_info )


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
