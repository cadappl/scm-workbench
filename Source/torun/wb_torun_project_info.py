'''
 ====================================================================
 Copyright (c) 2010-2011 ccc. All right reserved.

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
import wb_tree_panel
import wb_utils
import wb_manifest_providers

import wb_source_control_providers
import wb_subversion_list_handler
import wb_subversion_project_info

wc_path_browse_id = wx.NewId()
wc_path_text_ctrl_id = wx.NewId()
name_text_ctrl_id = wx.NewId()

class ProjectState:
    def __init__( self ):
        self.name = ''
        self.wc_path = ''
        self.color = ''
        self.manifest = ''
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
            manifest=self.state.manifest,
            wc_path=os.path.expanduser( self.state.wc_path ),
            menu_info=self.project_info.menu_info )

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
        raise wb_exceptions.InternalError( 'must override initControls' )

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

        self.wc_path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse...") )

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
            self.list_background_colour = ( 255,255,255 )

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

        self.manifest_ctrl = wx.TextCtrl( self, -1, size=(-1, 200), style=wx.HSCROLL|wx.TE_MULTILINE|wx.TE_RICH2 )
        self.manifest_ctrl.SetFont(wx.Font(wb_config.point_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, wb_config.face))
        self.sizer.Add( self.manifest_ctrl, 1, wx.EXPAND|wx.ALL )
        self.manifest_edit = wx.Button( self, -1, T_(" Edit... ") )

        wx.EVT_BUTTON( self, self.manifest_edit.GetId(), self.OnEditConfigspec )
        self.sizer.Add( self.manifest_edit, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

        return self.sizer

    def updateControls( self ):
        self.manifest_ctrl.SetValue( self.project_info.manifest )

    def validate( self, state ):
        if self.manifest_ctrl.GetValue().strip() == '':
            wx.MessageBox( T_('Enter a configspec'), style=wx.OK|wx.ICON_ERROR );
            return False

        state.manifest = self.manifest_ctrl.GetValue().strip()
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

        repo_names = self.project_info.project_infos.keys()
        repo_map_list = self.app.prefs.getRepository().repo_map_list

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        self.list_box =  wx.ListCtrl( self, -1, wx.DefaultPosition,
                (-1, 225), wx.LC_REPORT )
        self.list_box.InsertColumn( 0, T_('Name') )
        self.list_box.SetColumnWidth( 0, 100 )

        self.list_box.InsertColumn( 1, T_('Location') )
        self.list_box.SetColumnWidth( 1, 400 )

        repo_names.sort(wb_utils.compare)
        for item in repo_names:
            index = self.list_box.GetItemCount()
            self.list_box.InsertStringItem( index, item )
            if repo_map_list.has_key( item ):
                self.list_box.SetStringItem( index, 1, repo_map_list[item] )
            else:
                item = self.list_box.GetItem( index )
                item.SetTextColour( wx.RED )
                self.list_box.SetItem( item )

                self.list_box.SetStringItem( index, 1, '<unknown>' )

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
    def __init__( self, app, parent, project_info ):
        self.app = app
        self.parent = parent
        self.project_info = project_info

        self.client = pysvn.Client()
        self.client.exception_style = 1
        self.client.commit_info_style = 1

        self.client.callback_get_login = wb_exceptions.TryWrapper( self.app.log, self.app.getCredentials )
        self.client.callback_get_log_message = wb_exceptions.TryWrapper( self.app.log, self.getLogMessage )

        self.client.callback_ssl_server_trust_prompt = wb_exceptions.TryWrapper( self.app.log, self.getServerTrust )

        self.initNotify()

        #==== add functions except checkout and update
        for func in ( 'add', 'cat', 'checkin', 'copy', 'copy2',
                      'diff', 'info', 'info2', 'list', 'log', 'ls', 'mkdir',
                      'move', 'remove', 'revert', 'propget', 'propset', 'proplist',
                      'root_url_from_path', 'status', 'switch' ):
            self.__dict__[func] = getattr( self.client, func )

    def getLogMessage( self ):
        return True, 'Torun Client'

    def initNotify( self ):
        self.client.callback_notify = wb_exceptions.TryWrapper( self.app.log, self.callback_notify )

    def checkout( self, *arg, **args ):
        self.updateWithManifest( True )
        # should update the repository info
        self.project_info.initRepositoryInfo()

    def update( self, *arg, **args ):
        self.updateWithManifest( False )

    def updateWithManifest( self, checkout=False ):
        pv = None
        repo_map_list = self.app.prefs.getRepository().repo_map_list
        # detect the manifest provider
        for pv in wb_manifest_providers.getProviders():
            pi = ProjectInfo( self.app, self.parent, None )
            pi.manifest = self.project_info.manifest
            if pv.require( pi ):
                break
        else:
            print 'Error: cannot detect the format of configspec, make sure it\'s normal'
            return

        # it's assumed the stored configspec is always correct
        dirs = list()
        # 1. find and check out all repositories
        for repo in pv.getRepositories() or list():
            # ignore the unmapped repositories
            if not repo_map_list.has_key( repo ): continue

            url = '%s/trunk' % repo_map_list[repo]
            wc_path = os.path.join( self.project_info.wc_path, repo )
            # build up the repository location with /trunk
            if not os.path.exists( wc_path ):
                self.app.foregroundProcess( self.app.setAction, ( ('Checkout %s...' % wc_path), ) )
                self.client.checkout( url, wc_path, depth=pysvn.depth.infinity,
                                      revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            dirs.append( wc_path )

        # 2. read extra repository-relative materials
        lastp = dict()
        extras = pv.getRepoExtras( self.project_info.wc_path, repo_map_list )
        for m in extras or list():
            url, wc_path = m.remotep, m.localp

            # avoid to add duplicated url
            if wc_path in dirs:
                continue

            # record the urls to inform the user
            if not lastp.has_key( wc_path ):
                if len( lastp.keys() ) > 0:
                    for p in lastp.keys():
                        print 'Warn: %s cannot match any of proposed urls: %s' % (
                              p, ','.join( lastp[p] ) )

                lastp[wc_path] = [ url ]
            else:
                lastp[wc_path].append( url )

            if not self.exists( url ):
                # print 'Error: URL %s is not existent' % url
                continue

            if not os.path.exists( wc_path ):
                os.makedirs( wc_path )

                self.app.foregroundProcess( self.app.setAction, ( ('Checkout %s...' % m.localp), ) )
                self.client.checkout( url, wc_path, depth=pysvn.depth.infinity,
                                      revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            elif not checkout:
                self.app.foregroundProcess( self.app.setAction, ( ('Update %s...' % m.localp), ) )
                self.client.update( wc_path, depth=pysvn.depth.empty,
                                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )

            lastp = dict()
            dirs.append( wc_path )

        # 3. update or switch directory according to the configspec
        while len( dirs ) > 0:
            wc_path = dirs.pop( 0 )

            # 3.1 get the URL from the path
            url = self.get_url_from_path( wc_path )
            # 3.2 get the target URL from the configspec
            # Configspec.match returns a url list of matched rules in order,
            # to handle the list, a loop is required to check each url.
            mlist = pv.match( repo_map_list, self.project_info.wc_path, wc_path )

            # 3.3 check the existence of urls in mlist and do switch
            for m in mlist or list():
                new_url = m.remotep

                if os.path.abspath( m.localp ) != wc_path \
                or ( not self.exists( new_url ) ):
                    continue

                if url != new_url:
                    self.app.foregroundProcess( self.app.setAction, ( ('Switch %s...' % wc_path), ) )
                    self.client.switch( wc_path, new_url, depth=pysvn.depth.infinity,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                elif not checkout:
                    self.app.foregroundProcess( self.app.setAction, ( ('Update %s...' % wc_path), ) )
                    self.client.update( wc_path, depth=pysvn.depth.empty,
                                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                break

            # 3.4 cache the directories in current directory
            for d in os.listdir( wc_path ):
                path = os.path.join( wc_path, d )
                if ( not d.startswith( '.' ) ) and os.path.isdir( path ):
                    dirs.append( path )

    def exists( self, filename ):
        ret = True
        try:
            dirs = self.client.ls( filename,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )
        except:
            ret = False

        return ret

    def get_url_from_path( self, filename ):
        info = self.client.info2( filename, recurse=False )[0][1]

        return info.URL

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
    def __init__( self, app, parent, manifest='' ):
        wb_source_control_providers.ProjectInfo.__init__( self, app, parent, 'torun' )
        self.url = None
        self.wc_path = None
        self.manifest = manifest
        self.app = app
        self.parent = self.parent
        # TODO: check the usage of need_checkout
        self.need_update = False
        self.need_checkout = True
        self.need_properties = False
        self.project_infos = dict()

    def __repr__( self ):
        return '<torun.ProjectInfo wc_path=%r>' % self.wc_path

    def init( self, project_name, **kws ):
        wb_source_control_providers.ProjectInfo.init( self, project_name )

        try_wrapper = wb_exceptions.TryWrapperFactoryWithExcept(
                          self.app.log_client_error, pysvn.ClientError )
        self.menu_info = \
            ( ( 0, None, None )
              ,( wb_ids.id_SP_Torun_ProcAdd,
                 try_wrapper( self.isDirToAddIdent ),
                 try_wrapper( self.Cmd_Torun_ProcAdd ) )
              ,( wb_ids.id_SP_Torun_ProcDelete,
                 try_wrapper( self.isDirToDeleteIdent ),
                 try_wrapper( self.Cmd_Torun_ProcDelete ) )
              ,( 0, None, None )
              ,( wb_ids.id_SP_Torun_ProcDevelop,
                 try_wrapper( self.isDirToDevelop ),
                 try_wrapper( self.Cmd_Torun_ProcDevel ) )
              ,( wb_ids.id_SP_Torun_ProcDeliver,
                 try_wrapper( self.isDirToDeliver ),
                 try_wrapper( self.Cmd_Torun_ProcDeliv ) )
              ,( wb_ids.id_SP_Torun_ProcRevert,
                 try_wrapper( self.isDirToRevert ),
                 try_wrapper( self.Cmd_Torun_ProcRevert ) )
            )

        self.wc_path = kws['wc_path']
        self.manifest = kws.get( 'manifest', '' )
        self.manifest_provider = kws.get( 'manifest_provider', '' )
        #if self.manifest_provider == None or len( self.manifest_provider ) == 0:
        #    # detect the manifest format with all manifest providers
        #    for pv in wb_manifest_providers.getProviders():
        #        pi = ProjectInfo( self.app, self.parent, None )
        #        pi.manifest = self.manifest
        #        if pv.require( pi ):
        #            self.manifest_provider = pv.name

        # if no manifest, it assumed to be configspec
        if self.manifest_provider == None or self.manifest_provider == '':
            self.manifest_provider = 'configspec'

        if not self.menu_info:
            self.menu_info = kws.get( 'menu_info', None )

        # FIXME: adjust the version control system according to the settings
        # need one client/project/thread
        self.client_bg = SubversionClient( self.app, self.parent, self )
        self.client_fg = SubversionClient( self.app, self.parent, self ) #pysvn.Client()

        self.initRepositoryInfo()

    def initRepositoryInfo( self ):
        self.need_checkout = False
        # build up the subversion project infos
        pv = wb_manifest_providers.getProvider( self.manifest_provider )
        if pv != None:
            pi = ProjectInfo( self.app, self.parent, None )
            pi.manifest = self.manifest
            if pv.require( pi ):
                # get the repositories
                for repo in pv.getRepositories() or list():
                    self.project_infos[repo] = None

                # get the repository extras
                for extra in pv.getRepoExtras( self.wc_path ) or list():
                    self.project_infos[extra.localp] = None

                for repo in self.project_infos.keys():
                    wc_path = os.path.abspath( os.path.join( self.wc_path, repo ) )
                    try:
                        url = self.client_bg.get_url_from_path( wc_path )
                        # create a temporary subversion project_name '@@repo_name'
                        self.project_infos[repo] = wb_subversion_project_info.ProjectInfo(
                                                            self.app, self.parent )
                        self.project_infos[repo].init( '@@%s' % repo, url=url,
                                                       wc_path=wc_path, menu_info=self.menu_info )
                    except:
                        self.need_update = True
                        self.need_checkout = True

    def initNotify( self ):
        self.notification_of_files_in_conflict = 0

        self.client_bg.initNotify()
        self.client_fg.initNotify()

    def getTagsUrl( self, rel_url ):
        if self.parent is not None:
            return self.parent.getTagsUrl( rel_url )
        return self.expandedLabelUrl( True, rel_url )

    def getBranchesUrl( self, rel_url ):
        if self.parent is not None:
            return self.parent.getBranchesUrl( rel_url )
        return self.expandedLabelUrl( False, rel_url )

    def expandedLabelUrl( self, is_label, rel_url ):
        label_url = ''

        # pick the branch or tags from relative svn.ProjectInfo
        repo = self.findRepository( rel_url )
        if repo:
            if is_label:
                label_url = self.project_infos[repo].tags_url
            else:
                label_url = self.project_infos[repo].branches_url

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

    def findRepository( self, url ):
        for name, repo in self.project_infos.items():
            if url.startswith( repo.url ) \
            or url.startswith( repo.branches_url ) \
            or url.startswith( repo.tags_url ):
                return name

        return None

    def getLabesInTags( self, repo_info, name ):
        labels = list()

        uname = name.upper()
        try:
            # 1. project_location/tags/U(name)-x/project/
            dirs =  self.client_bg.ls( repo_info.tags_url,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )

            prefix = '%s/%s' % ( repo_info.tags_url, uname )
            for item in dirs:
                if item.name.rfind(prefix) >= 0:
                    labels.append( item.name.split('/')[-1] )
        except:
            pass

        # 2. project_location/tags/U(project_name)/x/project/
        try:
            ls_str = '%s/%s' % ( repo_info.tags_url, uname )
            dirs =  self.client_bg.ls( ls_str,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )

            for item in dirs:
                labels.append( '%s-%s' % ( uname, item.name.split('/')[-1] ) )
        except:
            pass

        return labels

    def readPreferences( self, get_option ):
        wb_source_control_providers.ProjectInfo.readPreferences( self, get_option )

        # load state from a preference file
        name = get_option.getstr( 'name' )
        wc_path = get_option.getstr( 'wc_path' )


        if get_option.has( 'manifest' ):
            manifest = get_option.getstr( 'manifest' )
        else:
            manifest = ''

        if get_option.has( 'manifest_provider' ):
            manifest_provider = get_option.getstr( 'manifest_provider' )
        else:
            manifest_provider = ''

        # expand any ~/ or ~user/ in the path
        wc_path = os.path.expanduser( wc_path )
        self.init( name, wc_path=wc_path,
                   manifest=manifest,
                   manifest_provider=manifest_provider )

    def writePreferences( self, pref_dict ):
        # save state into a preference file
        wb_source_control_providers.ProjectInfo.writePreferences( self, pref_dict )

        pref_dict[ 'wc_path' ] = self.wc_path
        if len( self.manifest ):
            pref_dict[ 'manifest' ] = self.manifest
            pref_dict[ 'manifest_provider' ] = self.manifest_provider

        if len(self.manifest):
            # read the name from preferences
            manifest_name = self.app.prefs.getRepository().manifest_name
            wb_read_file.writeFileByLine( os.path.join( self.wc_path, manifest_name ), self.manifest )

    def isEqual( self, pi ):
        return (self.provider_name == pi.provider_name
            and self.wc_path == pi.wc_path)

    def isChild( self, pi ):
        # only the subdirectories would be judged as the children
        if type(pi) == types.StringType:
            # see if the wc path of the parent is a prefix of the child
            url = self.url + os.path.sep
            return pi[:len(wc_path)] == wc_path
        else:
            # see if the wc path of the parent is a prefix of the child
            wc_path = self.wc_path + os.path.sep
            return pi.wc_path[:len(wc_path)] == wc_path

    def getWorkingDir( self ):
        return self.wc_path

    def mayExpand( self ):
        return len( self.project_infos.keys() ) > 0

    def updateStatus( self ):
        for repo in self.project_infos:
            if self.project_infos[repo]:
                self.project_infos[repo].updateStatus()

    def setNeedProperties( self, need_properties ):
        self.need_properties = need_properties

    def getFilesStatus( self ):
        all_files_status = list()
        for repo in self.project_infos:
            if self.project_infos[repo]:
                file_status = self.project_infos[repo].getDirStatus()
                if file_status:
                    all_files_status.append( file_status )

        return all_files_status

    def getTreeFilesStatus( self ):
        all_tree_files_status = list()

        for repo in self.project_infos:
            if self.project_infos[repo]:
                tree_files_status = self.project_infos[repo].getDirStatus()
                if tree_files_status:
                    all_tree_files_status.append( tree_files_status )

        return all_tree_files_status

    def getDirStatus( self ):
        all_dir_status = None

        # FIXME: check the function
        for repo in self.project_infos:
            if self.project_infos[repo]:
                dir_status = self.project_infos[repo].getDirStatus()
                # it just needs one status
                if dir_status and len(dir_status) > 0:
                    all_dir_status = dir_status
                    break

        return all_dir_status

    def replaceEscapeString( self, dirname, list_str ):
        # two alternatives are defined: %D %F, %R
        dirname = dirname.replace( '\\', '/' )
        if dirname.endswith( '/' ):
            dirname = dirname[ :len(dirname) - 1 ]

        basename = dirname.split( '/' )[-1]

        list_str = list_str.replace( '%D', dirname )
        list_str = list_str.replace( '%F', basename )
        list_str = list_str.replace( '%R', self.wc_path )

        return list_str

    def isInCheckList( self, dirname, list_str ):
        new_str = self.replaceEscapeString( dirname, list_str )
        items = new_str.split()

        for item in items:
            if os.path.exists(item):
                return True

        return False

    def isDirMatchParent( self, file_path ):
        ret, context = False, ''

        p = self.app.prefs.getRepository()
        #= check module's parent directory
        if re.match( p.info_module['parent'], file_path ):
            ret, context = ( True, 'module' )
        #= check package's parent directory
        if (not ret) and re.match( p.info_package['parent'], file_path ):
            ret, context = ( True, 'package' )

        # check project's parent directory
        if (not ret) and re.match( p.info_project['parent'], file_path ):
            ret, context = ( True, 'project' )

        return ret, context

    def isDirMatchPattern( self, file_path ):
        ret, context = False, ''

        wc_path = file_path.replace( '\\', '/' )
        p = self.app.prefs.getRepository()
        # check module's directory
        if self.isInCheckList( wc_path, p.info_module['pattern'] ):
            ret, context = True, 'module'
        # check package's directory
        if (not ret) and self.isInCheckList( wc_path, p.info_package['pattern'] ):
            ret, context = True, 'package'
        # check project's directory
        if (not ret) and self.isInCheckList( wc_path, p.info_project['pattern'] ):
            ret, context = True, 'project'

        return ret, context

    def isDirToAddIdent( self, project_info ):
        ret, context = self.isDirMatchParent( project_info.wc_path )

        return ret, 'Add %s...' % context

    def isDirToDeleteIdent( self, project_info ):
        wc_path = project_info.wc_path.replace( '\\', '/' )

        ret, context = self.isDirMatchPattern( wc_path )
        # check the parent directory even the identifier directory is empty
        if not ret:
            ret, context = self.isDirMatchParent( wc_path[:wc_path.rfind( '/' )] )

        if ret:
            context = "Delete %s '%s'" % (context, wc_path[wc_path.rfind( '/' ) + 1:])

        return ret, context

    def isDirToDevelop( self, project_info ):
        # 1. it should be an identifier directory
        ret, _ = self.isDirToDeleteIdent( project_info )
        if ret:
            # 2. check the file status
            file_status = self.client_fg.status( project_info.wc_path, recurse=False, ignore=False )
            state = self.getFileStatus( file_status )
            ret = (not state.modified) \
                  and (not state.new_versioned) \
                  and state.versioned \
                  and (not state.unversioned) \
                  and (not state.need_checkin) \
                  and (not state.need_checkout) \
                  and (not state.conflict) \
                  and state.file_exists

        if ret:
            # 3. check the file status
            props = self.readOrWriteSpecifiedProperties( project_info.wc_path )
            ret = props.get('status') != 'EXPERIMENTAL'

        return ret, 'kSVN Develop'

    def isDirToDeliver( self, project_info ):
        # 1. it should be an identifier directory
        ret, _ = self.isDirToDeleteIdent( project_info )
        if ret:
            # 2. check the file status
            file_status = self.client_fg.status( project_info.wc_path, recurse=True, ignore=False )
            state = self.getFileStatus( file_status )
            ret = (not state.modified) \
                  and (not state.new_versioned) \
                  and state.versioned \
                  and (not state.unversioned) \
                  and (not state.need_checkin) \
                  and (not state.need_checkout) \
                  and (not state.conflict) \
                  and state.file_exists

        if ret:
            # 3. check the file status
            props = self.readOrWriteSpecifiedProperties( project_info.wc_path )
            ret = props.get('status') == 'EXPERIMENTAL'

        return ret, 'kSVN Deliver'

    def isDirToRevert( self, project_info ):
        # 1. it should be an identifier directory
        ret, _ = self.isDirToDeleteIdent( project_info )
        if ret:
            # 2. check the file status
            file_status = self.client_fg.status( project_info.wc_path, recurse=True, ignore=False )
            state = self.getFileStatus( file_status )
            ret = state.modified and state.revertable

        if ret:
            # 3. check the file status
            props = self.readOrWriteSpecifiedProperties( project_info.wc_path )
            ret = props.get('status') == 'EXPERIMENTAL'

        return ret, 'kSVN Revert'

    def Cmd_Torun_ProcAdd( self, project_info ):
        repo_info = self.findRepository( project_info.url )
        if repo_info is None:
            return

        wc_path = project_info.wc_path.replace( '\\', '/' )
        ret, ident_type = self.isDirMatchParent( wc_path )

        if not ret:
            return

        ident_url, tailing_dir, local_ident = self.splitDirectory( repo_info, project_info )
        dir_name = os.path.basename( local_ident )

        # 1. it's under 'tags' directory
        if project_info.url.startswith( repo_info.tags_url ):
            # info to input a new tags label
            tag_list = self.getLabesInTags( repo_info, dir_name )
            rc, name, tag = self.app.getIdent( T_('Make new %s' % ident_type), dir_name, tag_list )
            if not rc:
                return

            # check the temporary directory for the process
            temp_dir = self.temporaryDevelopBranch( repo_info, self.project_name, name )
            if self.client_bg.exists( temp_dir ):
                wx.MessageBox( T_('Temporary is existent: %s' % temp_dir), style=wx.OK|wx.ICON_ERROR )
                return

            local_dir = os.path.join( project_info.wc_path, name )
            if os.path.exists( local_dir ):
                wx.MessageBox( T_('new path is existent: %s' % local_dir), style=wx.OK|wx.ICON_ERROR )
                return

            # 1.1 copy the SCIs to the new tag directory and make the new ident
            tag_dir = '%s/%s/%s' % ( repo_info.tags_url, tag, dir_name )
            self.client_bg.copy2( self.__listCopy( ident_url ), tag_dir, make_parents=True )
            # 1.2 create the new identifier in the repository directly
            new_dir = '%s/%s/%s' % ( tag_dir, tailing_dir, name )
            self.client_bg.mkdir( new_dir, 'kSVN ProcAdd' )
            # 1.3 switch the new tags
            self.client_bg.switch( local_ident, tag_dir, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )

            # 1.4 copy the new directory
            self.client_bg.copy2( self.__listCopy( new_dir ), temp_dir, make_parents=True )
            # 1.5 switch to the temp directory ...
            new_local = '%s/%s' % ( project_info.wc_path, name )
            self.client_bg.switch( new_local, temp_dir, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            # 1.6 create SCIs locally and don't submit
            self.createScisOnLocal( project_info, ident_type, local_dir )
        # 2. it's a trunk or branch, add the identifier directory directly
        else:
            rc, name = self.app.getFilename( T_('Make new %s' % ident_type), T_('Name:') )
            if not rc:
                return

            local_dir = os.path.join( project_info.wc_path, name )
            if os.path.exists( local_dir ):
                wx.MessageBox( T_('new path is existent: %s' % local_dir), style=wx.OK|wx.ICON_ERROR )
                return

            # check the temporary directory for the process
            temp_dir = self.temporaryDevelopBranch( repo_info, self.project_name, name )
            if self.client_bg.exists( temp_dir ):
                wx.MessageBox( T_('Temporary is existent: %s' % temp_dir), style=wx.OK|wx.ICON_ERROR )
                return

            # 2.1 create the new directory on the remote
            new_url = '%s/%s' % ( project_info.url, name )
            self.client_bg.mkdir( new_url, 'kSVN ProcAdd' )
            # 2.2 switch to the temp directory ...
            self.client_bg.copy2( self.__listCopy( new_url ), temp_dir, make_parents=True )
            self.client_bg.switch( local_dir, temp_dir, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            # 2.3 create SCIs locally but don't submit
            self.createScisOnLocal( project_info, ident_type, local_dir )

        self.app.refreshFrame()

    def Cmd_Torun_ProcDelete( self, project_info ):
        repo_info = self.findRepository( project_info.url )
        if repo_info is None:
            return

        wc_path = project_info.wc_path.replace( '\\', '/' )
        ret, ident_type = self.isDirMatchPattern( wc_path )
        if not ret:
            ret, ident_type = self.isDirMatchParent( wc_path[:wc_path.rfind( '/' )] )

        if not ret:
            return

        # 1. it's under 'tags' directory
        if project_info.url.startswith( repo_info.tags_url ):
            # 1.1 make sure the temporary directory could be used
            ident_url, tailing_dir, local_ident = self.splitDirectory( repo_info, project_info )
            dir_name = os.path.basename( local_ident )
            temp_dir = self.temporaryDevelopBranch( repo_info, self.project_name, dir_name )

            if self.client_bg.exists( temp_dir ):
                wx.MessageBox( T_('Temporary is existent: %s' % temp_dir), style=wx.OK|wx.ICON_ERROR )
                return

            # 1.2 create the temporary path
            temp_dir = self.temporaryDevelopBranch( repo_info, self.project_name, dir_name )
            # 1.3 copy the new directory
            self.client_bg.copy2( self.__listCopy( ident_url ), temp_dir, make_parents=True )
            # 1.4 switch to the temp directory ...
            self.client_bg.switch( local_ident, temp_dir, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            # 1.5 setup the properties
            properties['status'] = 'EXPERIMENTAL'
            properties['vsnorigin'] = self.relativePath( project_info.url )

            self.readOrWriteSpecifiedProperties( local_ident, properties )
            # 1.6 create SCIs locally and don't submit
            self.client_bg.remove( project_info.wc_path )

        # 2. it's a trunk or branch, remove the directory directly
        else:
            self.client_bg.remove( project_info.wc_path )

        self.app.refreshFrame()

    def Cmd_Torun_ProcDevel( self, project_info ):
        repo_info = self.findRepository( project_info.url )
        if repo_info is None:
            return

        wc_path = project_info.wc_path.replace( '\\', '/' )
        ret, ident_type = self.isDirMatchPattern( wc_path )
        if not ret:
            ret, ident_type = self.isDirMatchParent( wc_path[:wc_path.rfind( '/' )] )

        if not ret:
            return

        dir_name = os.path.basename( project_info.wc_path )
        ident_url, tailing_dir, local_ident = self.splitDirectory( repo_info, project_info )

        # check the temporary directory for the process
        temp_dir = self.temporaryDevelopBranch( repo_info, self.project_name, dir_name )
        if self.client_bg.exists( temp_dir ):
            wx.MessageBox( T_('Temporary is existent: %s' % temp_dir), style=wx.OK|wx.ICON_ERROR )
            return

        self.app.setAction( T_('Torun Developing process %s...') % project_info )

        yield self.app.backgroundProcess

        try:
            properties = self.readOrWriteSpecifiedProperties( local_ident )

            self.app.log.info( "Change workspace from %s to %s" % ( ident_url, temp_dir ) )
            # 1 copy the contents to the temporary directory ...
            self.client_bg.copy2( self.__listCopy( ident_url ), temp_dir, make_parents=True )
            # 2 switch to the temp directory ...
            self.client_bg.switch( local_ident, temp_dir, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            # 3. update the properties
            properties['status'] = 'EXPERIMENTAL'
            properties['vsnorigin'] = self.relativePath( project_info.url )

            self.readOrWriteSpecifiedProperties( local_ident, properties )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )
        self.app.refreshFrame()

    def Cmd_Torun_ProcDeliv( self, project_info ):
        repo_info = self.findRepository( project_info.url )
        if repo_info is None:
            return

        wc_path = project_info.wc_path.replace( '\\', '/' )
        ret, ident_type = self.isDirMatchPattern( wc_path )
        if not ret:
            ret, ident_type = self.isDirMatchParent( wc_path[wc_path.rfind( '/' )] )

        if not ret:
            return

        ident_url, tailing_dir, local_ident = self.splitDirectory( repo_info, project_info )
        properties = self.readOrWriteSpecifiedProperties( local_ident )
        if properties['status'] != 'EXPERIMENTAL':
            return

        self.app.setAction( T_('Torun delivering process %s...') % project_info )

        dir_name = os.path.basename( project_info.wc_path )
        tag_list = self.getLabesInTags( repo_info, dir_name )
        rc, tag = self.app.getIdent( T_('Make new %s' % ident_type), dir_name, tag_list, True )
        if rc:
            # 1. copy the SCIs to the new tag directory and make the new ident
            tag_dir = '%s/%s/%s' % ( repo_info.tags_url, tag, dir_name )
            # 2. update and submit the properties
            properties['status'] = 'CONFIDENTIAL'
            properties['vsnnumber'] = tag
            properties['vsnorigin'] = self.relativePath( project_info.url )

            yield self.app.backgroundProcess
            try:
                self.readOrWriteSpecifiedProperties( local_ident, properties )

                self.client_bg.checkin( local_ident, 'Torun Deliv', recurse=True )
                # 3. copy and switch to the new tag location
                self.client_bg.copy2( self.__listCopy( ident_url ), tag_dir, make_parents=True )
                # 4. create the new identifier in the repository directly
                self.client_bg.switch( local_ident, tag_dir, depth=pysvn.depth.infinity,
                                       revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
                # 5. remove the temporary location
                self.client_bg.remove( ident_url )
            except pysvn.ClientError, e:
                self.app.log_client_error( e )

            yield self.app.foregroundProcess

        self.app.clearProgress()
        self.app.setAction( T_('Ready') )

        self.app.refreshFrame()

    def Cmd_Torun_ProcRevert( self, project_info ):
        repo_info = self.findRepository( project_info.url )
        if repo_info is None:
            return

        wc_path = project_info.wc_path.replace( '\\', '/' )
        ret, ident_type = self.isDirMatchPattern( wc_path )
        if not ret:
            ret, ident_type = self.isDirMatchParent( wc_path[:wc_path.rfind( '/' )] )

        if not ret:
            return

        dir_name = os.path.basename( project_info.wc_path )
        ident_url, tailing_dir, local_ident = self.splitDirectory( repo_info, project_info )

        properties = self.readOrWriteSpecifiedProperties( local_ident )
        orginal_url = properties.get( 'vsnorigin' )
        if orginal_url is None:
            MessageBox( T_("vsnorigin '%s' is not existent" % orginal_url), style=wx.OK|wx.ICON_ERROR )
            return
        else:
            orginal_url = self.client_bg.root_url_from_path( project_info.url ) + orginal_url
            if not self.client_bg.exists( orginal_url ):
                MessageBox( T_("'vsnorigin' is not defined"), style=wx.OK|wx.ICON_ERROR )
                return

        # should not be equal
        if orginal_url == ident_url:
            MessageBox( T_("'vsnorigin' is equal with current url"), style=wx.OK|wx.ICON_ERROR )
            return

        self.app.setAction( T_('Torun reverting process %s...') % project_info )

        yield self.app.backgroundProcess
        try:
            # 1. revert the modfication if possible
            self.client_bg.revert( local_ident, recurse=True )
            # 2. create the new identifier in the repository directly
            self.client_bg.switch( local_ident, orginal_url, depth=pysvn.depth.infinity,
                                   revision=pysvn.Revision( pysvn.opt_revision_kind.head ) )
            # 3. remove the temporary location
            self.client_bg.remove( project_info.url )
        except pysvn.ClientError, e:
            self.app.log_client_error( e )

        yield self.app.foregroundProcess
        self.app.clearProgress()
        self.app.setAction( T_('Ready') )

        self.app.refreshFrame()

    def readOrWriteSpecifiedProperties( self, filename, value_dict=None ):
        ret = dict()
        props = ['status', 'vsnbranch', 'vsnnumber', 'vsnorigin']

        if isinstance( value_dict, dict ):
            for name, value in value_dict.items():
                name = 'svncm:%s' % name
                if value is not None:
                    self.client_bg.propset( name, value, filename )
        else:
            prop_list = self.client_bg.proplist( filename,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.working ) )
            if len( prop_list ) == 0:
                prop_dict = {}
            else:
                _, prop_dict = prop_list[0]

            for name in props:
                k = 'svncm:%s' % name
                ret[name] = prop_dict.get( k, None )

        return ret

    def temporaryDevelopBranch( self, project_info, project_name, directory ):
        dir_name = directory.split( '/' )[-1]

        return '%s/SvnCM/%s/%s' % ( project_info.branches_url, project_name, dir_name )

    def relativePath( self, url ):
        try:
            root_dir = self.client_bg.root_url_from_path( url )
            new_path = url[len( root_dir ):]
        except:
            new_path = url

        return new_path

    def createScisOnLocal( self, repo_info, ident_type, new_dir ):
        p = self.app.prefs.getRepository()

        if ident_type == 'module':
            component = p.info_module['component']
        elif ident_type == 'package':
            component = p.info_package['component']
        elif ident_type == 'project':
            component = p.info_project['component']

        dirs = list()
        files = list()

        item_list = self.replaceEscapeString( new_dir, component )
        for item in item_list.split():
            if item.find( '.' ) >= 0:
                files.append( os.path.join( new_dir, item ) )
            else:
                dirs.append( os.path.join( new_dir, item ) )

        self.client_bg.mkdir( dirs, 'kSVN SCIs_Creation' )
        for f in files:
            wb_read_file.writeFileByLine( f, '' )

        self.client_bg.add( files )
        properties = dict( { 'status':'EXPERIMENTAL'} )

        self.readOrWriteSpecifiedProperties( new_dir, properties )

    def splitDirectory( self, repo_info, project_info ):
        ident_url = ''
        repo_dir = repo_info.wc_path.replace( '\\', '/' )
        tailing_dir = local_dir = project_info.wc_path.replace( '\\', '/' )

        while local_dir != '' and local_dir != repo_dir:
            parent_dir = local_dir[:local_dir.rfind( '/' )]
            # check both current directory its parent
            ret, _ = self.isDirMatchPattern( local_dir )
            if not ret:
                ret, _ = self.isDirMatchParent( parent_dir )

            if ret:
                break
            local_dir = parent_dir

        if os.path.exists( local_dir ):
            ident_url = self.client_bg.get_url_from_path( local_dir )

        tailing_dir = tailing_dir[len( local_dir ) + 1:]

        return ident_url, tailing_dir, local_dir

    def getFileStatus( self, all_files_status ):
        all_files_status.sort( wb_subversion_utils.by_path )

        file_status = all_files_status[0]

        state = wb_tree_panel.TreeState()
        if file_status is None:
            state.modified = False
            state.new_versioned = False
            state.versioned = True
            state.unversioned = False
            state.need_checkin = False
            state.need_checkout = True
            state.conflict = False
            state.file_exists = False
            state.revertable = False
        else:
            state.versioned = True
            state.unversioned = True
            state.need_checkout = False
            state.file_exists = True

            if not os.path.exists( file_status.path ):
                state.file_exists = False

            text_status = file_status.text_status
            if text_status in [pysvn.wc_status_kind.unversioned, pysvn.wc_status_kind.ignored]:
                state.versioned = False
            else:
                state.unversioned = False

            state.new_versioned = state.new_versioned and text_status in [pysvn.wc_status_kind.added]

            prop_status = file_status.prop_status
            state.modified = (text_status in [pysvn.wc_status_kind.modified,
                                                pysvn.wc_status_kind.conflicted]
                            or
                                prop_status in [pysvn.wc_status_kind.modified,
                                                pysvn.wc_status_kind.conflicted])
            state.need_checkin = (text_status in [pysvn.wc_status_kind.added,
                                                    pysvn.wc_status_kind.deleted,
                                                    pysvn.wc_status_kind.modified]
                                or
                                    prop_status in [pysvn.wc_status_kind.added,
                                                    pysvn.wc_status_kind.deleted,
                                                    pysvn.wc_status_kind.modified])
            state.conflict = text_status in [pysvn.wc_status_kind.conflicted]

            state.revertable = state.conflict or state.modified or state.need_checkin or not state.file_exists

        return state

    def __listCopy( self, file_list ):
        if isinstance( file_list, ( list, tuple ) ):
            return [ file_list ]
        else:
            return [ (file_list, ) ]

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
