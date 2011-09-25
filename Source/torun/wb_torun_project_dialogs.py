'''
 ====================================================================
 Copyright (c) 2010-2011 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_project_dialogs.py

'''
import wx
import wx.wizard
# import wb_torun_configspec
import wb_source_control_providers
import wb_manifest_providers

import pysvn
import os

import wb_config
import wb_read_file

wc_path_browse_id = wx.NewId()
wc_path_text_ctrl_id = wx.NewId()
name_text_ctrl_id = wx.NewId()
url_trunk_path_text_ctrl_id = wx.NewId()
url_tags_path_text_ctrl_id = wx.NewId()

wizard_id = wx.NewId()

class _TinyEditor(wx.Dialog):
    def __init__( self, parent, title, text='' ):
        wx.Dialog.__init__( self, parent, -1, title,
          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.FIXED_MINSIZE )

        sizer = wx.BoxSizer( wx.VERTICAL )
        self.textctrl = wx.TextCtrl( self, -1, text,
                        size=( 500, 400 ),
                        style=wx.HSCROLL|wx.TE_MULTILINE|wx.TE_RICH2 )

        self.textctrl.SetFont( wx.Font( wb_config.point_size, wx.DEFAULT,
                                        wx.NORMAL, wx.NORMAL, False, wb_config.face ) )

        sizer.Add( self.textctrl, 1, wx.ALL|wx.EXPAND, 5 )
        sizer.Add( wx.StaticLine( self, -1, size=( 20,-1 ), style=wx.LI_HORIZONTAL ),
                   0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_BOTTOM|wx.ALL, 5 )
        sizer.Add( self.CreateStdDialogButtonSizer( wx.OK | wx.CANCEL ),
                   0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM|wx.ALL, 5 )

        self.SetSizer( sizer )
        self.Fit()

    def GetValue( self ):
        return self.textctrl.GetValue()

class AddProjectDialog:
    def __init__( self, app, parent ):
        self.app = app

        self.provider_name = 'torun'

        # get the list of names to use in the validation
        pi_list = self.app.prefs.getProjects().getProjectList()
        self.pi_names = [pi.project_name for pi in pi_list]

        self.wizard = wx.wizard.Wizard( parent, wizard_id, T_("Add Torun Project") )

        self.page_wc_choice = WorkingCopyChoicePage( self )
        self.page_wc_exists = WorkingCopyExistsPage( self )
        self.page_url = SubversionUrlPage( self )

        self.page_project_name = ProjectNamePage( self )
        self.page_new_project = ProjectNamePage( self )

        self.page_mf_choice = ProjectSelectionPage( self )
        self.page_directory = DirectoryPage( self )

        self.page_wc_choice.SetNext( self.page_project_name )

        self.page_wc_exists.SetPrev( self.page_wc_choice )
        self.page_wc_exists.SetNext( self.page_new_project )
        self.page_new_project.SetPrev( self.page_wc_exists )

        self.page_url.SetPrev( self.page_wc_choice )

        self.page_mf_choice.SetPrev( self.page_wc_choice )
        self.page_mf_choice.SetNext( self.page_directory )
        self.page_directory.SetPrev( self.page_mf_choice )

        self.wizard.FitToPage( self.page_wc_exists )

        self.wizard.Bind( wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged )
        self.wizard.Bind( wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging )

        self.state = wb_source_control_providers.AddProjectState()

    def ShowModal( self ):
        self.page_wc_choice.loadState( self.state )

        if self.wizard.RunWizard( self.page_wc_choice ):
            return wx.ID_OK
        return wx.ID_CANCEL

    def getProjectInfo( self ):
        provider = wb_source_control_providers.getProvider( self.provider_name )

        pi = provider.getProjectInfo( self.app )
        pi.init( self.state.project_name,
                 wc_path=self.state.wc_path,
                 manifest=self.state.manifest,
                 url=self.state.url_path )

        return pi

    def OnPageChanged( self, event ):
        page = event.GetPage()
        page.loadState( self.state )

    def OnPageChanging( self, event ):
        page = event.GetPage()
        if event.GetDirection():
            if not page.saveState( self.state ):
                event.Veto()

    def setProviderName( self, provider_name):
        self.provider_name = provider_name
        provider = wb_source_control_providers.getProvider( self.provider_name )

        pi = provider.getProjectInfo( self.app )

        pi.init( '', wc_path='', url='' )
        self.client_pi = pi

#----------------------------------------------------------------------
def makePageTitle(wizPg, title):
    sizer = wx.BoxSizer(wx.VERTICAL)
    wizPg.SetSizer(sizer)
    title = wx.StaticText(wizPg, -1, title)
    title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
    sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
    sizer.Add(wx.StaticLine(wizPg, -1), 0, wx.EXPAND|wx.ALL, 5)
    return sizer

#----------------------------------------------------------------------

class TitledPage(wx.wizard.PyWizardPage):
    def __init__(self, parent, title):
        wx.wizard.PyWizardPage.__init__(self, parent.wizard)
        self.parent = parent
        self.sizer = makePageTitle(self, title)
        self.next = None
        self.prev = None

    def SetNext( self, next ):
        self.next = next

    def SetPrev( self, prev ):
        self.prev = prev

    def GetNext( self ):
        return self.next

    def GetPrev( self ):
        return self.prev

    def loadState( self, state ):
        pass

    def saveState( self, state ):
        return True

class WorkingCopyChoicePage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Working Copy") )
        self.radio_new = wx.RadioButton( self, -1, T_(" Create new Torun project "), style = wx.RB_GROUP )
        self.radio_existing = wx.RadioButton( self, -1, T_(" Use existing Torun project ") )

        self.sizer.Add( (10, 50) )
        self.sizer.Add( self.radio_new, 0, wx.ALL, 5 )
        self.sizer.Add( (5, 5) )
        self.sizer.Add( self.radio_existing, 0, wx.ALL, 5 )

    def GetNext( self ):
        if self.radio_new.GetValue():
            return self.parent.page_mf_choice
        if self.radio_existing.GetValue():
            return self.parent.page_wc_exists

        return None

    def loadState( self, state ):
        self.radio_new.SetValue( state.use_existing == 0 )
        self.radio_existing.SetValue( state.use_existing == 1 )

    def saveState( self, state ):
        if self.radio_new.GetValue():
            state.use_existing = 0
        elif self.radio_existing.GetValue():
            state.use_existing = 1

        return True

class WorkingCopyExistsPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Working Copy") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.wc_path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.wc_path_ctrl = wx.TextCtrl(self, wc_path_text_ctrl_id, '' )
        self.wc_path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse... ") )

        self.g_sizer.Add( self.wc_path_label, 0, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 5 )
        self.g_sizer.Add( self.wc_path_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 3 )
        self.g_sizer.Add( self.wc_path_browse, 0, wx.EXPAND )

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

        self.url_label = wx.StaticText( self, -1, T_('Subversion URL:'), style=wx.ALIGN_RIGHT )
        self.url_ctrl = wx.StaticText( self, -1, '' )

        self.g_sizer.Add( self.url_label, 0, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 5 )
        self.g_sizer.Add( self.url_ctrl, 0, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 5 )
        self.g_sizer.Add( (1, 1), 0, wx.EXPAND )

        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

        wx.EVT_BUTTON( self, wc_path_browse_id, self.OnBrowseWorkingCopyDir )
        wx.EVT_TEXT( self, wc_path_text_ctrl_id, self.updateControls )

        self.manifest = None
        self._update_controls_lock = False

    def loadState( self, state ):
        self.wc_path_ctrl.SetValue( state.wc_path )
        self.updateControls()

    def saveState( self, state ):
        # must get the abspath to convert c:/dir1/dir2 to c:\dir1\dir2
        # otherwise all sorts of things break inside workbench
        state.wc_path = os.path.abspath( os.path.expanduser( self.wc_path_ctrl.GetValue().strip() ) )
        state.url_path = self.url_ctrl.GetLabel().strip()

        state.manifest = self.manifest

        if not os.path.exists( state.wc_path ):
            wx.MessageBox( T_('Path %s\n'
                    'Does not exist\n'
                    'Choose an existing Torun working copy directory')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
            return False

        if not os.path.isdir( state.wc_path ):
            wx.MessageBox( T_('Path %s\n'
                    'Is not a directory\n'
                    'Choose an existing Torun working copy directory')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
            return False

        if state.url_path == '' and state.manifest is None:
            wx.MessageBox( T_('Path %s\n'
                    'Is not a Torun working copy\n'
                    'Choose an existing Torun working copy directory')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
            return False

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

    def updateControls( self, event=None ):
        # on some platforms we will be reentered when SetValue is called
        if self._update_controls_lock:
            return

        self._update_controls_lock = True
        self.parent.setProviderName( 'torun' )

        # If the wc_path exists and is a svn wc then disable the url field
        wc_path = os.path.expanduser( self.wc_path_ctrl.GetValue() )

        if os.path.exists( wc_path ):
            p = self.parent.app.prefs.getRepository()
            manifestf = os.path.join( wc_path, p.manifest_name )
            if os.path.exists( manifestf ):
                manifest = wb_read_file.readFile( manifestf )
                # detect the manifest format with all manifest providers
                for pv in wb_manifest_providers.getProviders():
                    pi = wb_source_control_providers.ProjectInfo( self.parent.app, self.parent, None )
                    pi.manifest = manifest
                    if pv.require( pi ):
                        self.manifest = manifest

        self._update_controls_lock = False

class SubversionUrlPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Subversion URL") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )


        self.url_path_label = wx.StaticText( self, -1, T_('Subversion URL:'), style=wx.ALIGN_RIGHT )
        self.url_path_ctrl = wx.TextCtrl( self, url_trunk_path_text_ctrl_id, '' )

        self.url_repo_button = wx.Button( self, -1, T_('...') )

        self.g_sizer.Add( self.url_path_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.url_path_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        self.g_sizer.Add( self.url_repo_button, 0 )

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

        wx.EVT_BUTTON( self, self.url_repo_button.GetId(), self.OnEventRepoButton )

        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

    def OnEventRepoButton( self, event ):
        new_url = self.parent.app.getRepositoryPath( self.parent.wizard,
                                                     self.url_path_ctrl.GetValue() )
        if new_url:
            self.url_path_ctrl.SetValue( new_url )

    def loadState( self, state ):
        self.url_path_ctrl.SetValue( state.wc_path )

    def saveState( self, state ):
        self.parent.setProviderName( 'torun' )

        state.url_path = self.url_path_ctrl.GetValue().strip()

        if state.url_path == '':
            wx.MessageBox( T_('Enter a Subversion URL'), style=wx.OK|wx.ICON_ERROR );
            return False

        if not self.parent.client_pi.client_fg.is_url( state.url_path ):
            wx.MessageBox( T_('%s is not a valid Subversion URL') % state.url_path,
                           style=wx.OK|wx.ICON_ERROR );
            return False

        try:
            head = pysvn.Revision( pysvn.opt_revision_kind.head )
            self.parent.client_pi.client_fg.log( state.url_path, revision_start=head, revision_end=head )
        except pysvn.ClientError, e:
            wx.MessageBox( T_('%(url)s is not a accessable Subversion URL\n'
                                '%(error)s') %
                            {'url': state.url_path
                            ,'error': e.args[0]},
                style=wx.OK|wx.ICON_ERROR )

            return False

        return True

class ProjectSelectionPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Configspec") )

        self.manifest = ''
        self.repo_list = None

        self.client = pysvn.Client()
        self.client.exception_style = 1

        # choose for creation type
        radiobox_type = wx.RadioBox( self, -1, "Creation Type", wx.DefaultPosition, wx.DefaultSize,
                                     ( 'Create with Manual Manifest', 'Create with Baseline info' ),
                                     2, wx.RA_SPECIFY_COLS )

        radiobox_type.Bind( wx.EVT_RADIOBOX, self.OnChangeConfigspecCategory)
        self.sizer.Add( radiobox_type, 0, wx.EXPAND|wx.ALL, 5 )

        text_proj_id = wx.StaticText( self, -1, T_("Project ID") )
        self.project_id = wx.ComboBox( self, -1, style=wx.CB_READONLY )
        text_proj_label = wx.StaticText( self, -1, T_("Project Label") )
        self.project_label = wx.ComboBox( self, -1, style=wx.CB_READONLY )
        self.extend_proj = wx.CheckBox( self, -1, T_("Include Extended Projects") )

        info_sizer = wx.StaticBoxSizer( wx.StaticBox( self, -1, T_( "Baseline Info" ) ), wx.VERTICAL )
        prj_sizer = wx.FlexGridSizer( 0, 4, 0, 0 )
        prj_sizer.AddGrowableCol( 1 )
        prj_sizer.AddGrowableCol( 3 )
        prj_sizer.Add( text_proj_id, 0, wx.EXPAND|wx.ALL, 1 )
        prj_sizer.Add( self.project_id, 0, wx.EXPAND|wx.ALL, 1 )
        prj_sizer.Add( text_proj_label, 0, wx.EXPAND|wx.ALL, 1 )
        prj_sizer.Add( self.project_label, 0, wx.EXPAND|wx.ALL, 1 )

        info_sizer.Add( prj_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        info_sizer.Add( self.extend_proj, 0, wx.ALL, 5 )
        self.sizer.Add( info_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        spec = wx.StaticBox( self, -1, T_("Manifest") )
        spec_sizer = wx.StaticBoxSizer( spec, wx.HORIZONTAL )
        spec_text = wx.StaticText( self, -1, T_("The manifest format must obey SIG definitions") )
        self.spec_button = wx.Button( self, -1, T_("Manifest") )

        spec_sizer.Add( spec_text, 0, wx.EXPAND|wx.ALL, 5 )
        spec_sizer.Add( self.spec_button, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )
        self.sizer.Add( spec_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        self.extend_proj.Bind( wx.EVT_CHECKBOX, self.OnSelectExtendedProject )
        self.project_id.Bind( wx.EVT_COMBOBOX, self.OnProjectIdChange )
        self.project_label.Bind( wx.EVT_COMBOBOX, self.OnProjectLabelChange )
        self.spec_button.Bind( wx.EVT_BUTTON, self.OnConfigspecClick )

    def loadState( self, state ):
        self.manifest = state.manifest
        # delay to load the project info in remote
        self.updateControls(0)

    def saveState( self, state ):
        self.parent.setProviderName( 'torun' )

        if self.manifest == '':
            wx.MessageBox( T_('Select a project with one specified version, or enter a configspec'),
                           style=wx.OK|wx.ICON_ERROR );
            return False

        error = None
        for pv in wb_manifest_providers.getProviders() or list():
            pi = wb_source_control_providers.ProjectInfo( self.parent.app, self.parent, None )
            pi.manifest = self.manifest
            if pv.require( pi ):
                break
        else:
            wx.MessageBox( 'None of supported manifest provider knows the format',
                           style=wx.OK|wx.ICON_ERROR )
            return False

        state.manifest = self.manifest
        state.project_name = self.project_id.GetClientData( self.project_id.GetSelection() )

        return True

    def OnChangeConfigspecCategory( self, event ):
        choice = event.GetInt()

        self.updateControls( choice )

    def OnSelectExtendedProject( self, event ):
        self.updateControls( self.choice, True )

    def OnProjectIdChange( self, event ):
        project = self.project_id.GetClientData( self.project_id.GetSelection() )
        if project == None:
            return

        uproject = project.upper()
        project_location = self.repo_list.get( project )
        if not project_location:
            return

        dir_maps = dict()
        prefix = self.parent.app.prefs.getRepository().repo_prefix
        if prefix[-1] != '/':
            prefix += '/'

        repo_name = ( project_location.replace( prefix, '' ).split( '/' ) )[0]
        repo_location = self.repo_map.get( repo_name )
        if not repo_location:
            return

        if not repo_location.endswith( '/' ):
            repo_location += '/'

        # try to read all project tags. compatible with Torun - two
        # types of path could be formed:
        # 1. project_location/tags/U(project_name)-x/project/
        try:
            ls_str = '%stags/' % repo_location
            dirs =  self.client.ls( ls_str,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )

            for item in dirs:
                if item.name.rfind( '/tags/%s-' % uproject ) > 0:
                    label = item.name.split( '/' )[-1]
                    dir_maps[ label ] = item.name
        except:
            # ignore the exception
            pass

        # 2. project_location/tags/U(project_name)/x/project/
        try:
            ls_str = '%stags/%s' % ( repo_location, uproject )
            dirs =  self.client.ls( ls_str,
                    recurse=False,
                    revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                    peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ) )

            for item in dirs:
                label = '%s-%s' % ( uproject, item.name.split('/')[-1] )
                dir_maps[ label ] = item.name
        except:
            # ignore the exception
            pass

        self.project_label.Clear()
        if len( dir_maps ) > 0:
            dir_list = dir_maps.keys()

            # sort without CB_LIST
            dir_list.sort()
            for item in dir_list:
                self.project_label.Append( item, dir_maps[item] )

            self.project_label.SetSelection( 0 )
            self.OnProjectLabelChange( None )

    def OnProjectLabelChange( self, event ):
        self.manifest = ''
        location = self.project_label.GetClientData( self.project_label.GetSelection() )

        # read the configspec with the order defined in the list
        project = self.project_id.GetClientData( self.project_id.GetSelection() )

        for name in ( 'configspec', 'config_spec', 'configspec.linux',
                      'configspec.cygwin', 'configspec.windows' ):
            try:
                url = '%s/%s/confm/%s' % ( location, project, name )
                manifest = self.client.cat(url,
                           revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                           peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified) )

                # a manifest editor is requested to edit the manifest
                # according to different manifest format.
                editor = None
                # build up a new manifest with selected labels
                for p in wb_manifest_providers.getProviders() or list():
                    pi = wb_source_control_providers.ProjectInfo( self.parent.app, self.parent, p.name )
                    pi.manifest = manifest
                    if p.require( pi ):
                        editor = p.getEditor()
                        break
                else:
                    # consider the empty configspec as a normal one to insert the project info
                    if len( manifest ) == 0:
                        p = wb_manifest_providers.getProvider( 'configspec' )
                        editor = p.getEditor()

                if editor != None:
                    # insert the comments
                    editor.insert( 0, '#====================================' )
                    editor.insert( 1, '# Generated from %s' % name )
                    editor.insert( 2, '#====================================' )
                    # it needn't insert an empty line for an empty manifest
                    if len( manifest ) != 0:
                        editor.insert( 3, '' )
                    # add the project
                    editor.append( '')
                    editor.append( '#===+PROJECT' )
                    editor.append( '%s/%s/...' % (self.repo_list[project], project ),
                                   self.project_label.GetValue() )

                    self.manifest = editor.getManifest()
                break
            except:
                pass

        self.updateControls( self.choice )

    def OnConfigspecClick( self, event ):
        editor = _TinyEditor( self, 'Edit Manifest', self.manifest )
        if editor.ShowModal() == wx.ID_OK:
            self.manifest = editor.GetValue()
            editor.Destroy()

    def updateControls( self, choice, force=False ):
        self.choice = choice

        if self.repo_list is None:
            p = self.parent.app.prefs.getRepository()
            self.repo_map = p.repo_map_list
            self.repo_list = self._readRepoList( p.repo_baseline )

        # don't re-create the combox if it's inited and not required
        if not force:
            force = len( self.project_id.GetValue() ) == 0

        is_torun_p = choice == 1 and len( self.repo_list ) > 0

        self.project_id.Enable( is_torun_p )
        self.project_label.Enable( is_torun_p )
        self.extend_proj.Enable( is_torun_p )

        if is_torun_p and force:
            self.project_id.Clear()

            # sort the project list without CB_SORT
            def cmp_by_name( a, b ):
                return cmp( a[0], b[0] )

            item_list = list()
            for item in self.repo_list.keys():
                if item.startswith( 'vy' ):
                    value = item.replace( 'vy', 'VY' )
                else:
                    value = item

                item_list.append( ( value, item ) )

            item_list.sort( cmp_by_name )
            for value, item in item_list:
                if self.extend_proj.IsChecked():
                    self.project_id.Append( value, item )
                # only the project leading with VY are standard SiG project
                elif value.startswith( 'VY' ):
                    self.project_id.Append( value, item )

            self.project_id.SetSelection( 0 )
            self.OnProjectIdChange( None )

        # set enable with a usable manifest
        self.spec_button.Enable( len( self.manifest ) > 0 )

    def _readRepoList( self, repo_url ):
        ret = dict()

        repo_url = repo_url.replace( '\\', '/' )
        if not repo_url.endswith( '/' ):
            repo_url += '/'

        text = None
        for suffix in ['trunk/' + ( repo_url.split( '/' ) )[-2] + '/repo.list',
                       'trunk/baseline/repo.list',
                       'trunk/repo.list',
                       'repo.list']:
            try:
                text = self.client.cat( repo_url + suffix,
                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                        peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified) )
            except:
                # don't handle any exception
                pass
            finally:
                if text != None: break

        if text:
            for li in text.split( '\n' ):
                li = li.strip()

                if li.startswith( '#' ): continue
                a = li.strip().split()
                if len(a) > 1:
                    ret[ a[0] ] = a[1]

        return ret

class DirectoryPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Directory") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )

        self.path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.path_ctrl = wx.TextCtrl(self, wc_path_text_ctrl_id, '' )
        self.path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse... ") )

        self.g_sizer.Add( self.path_label, 0, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 5 )
        self.g_sizer.Add( self.path_ctrl, 1, wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, 3 )
        self.g_sizer.Add( self.path_browse, 0, wx.EXPAND )

        self.g_sizer.Add( ( 10, 10 ) )
        self.g_sizer.Add( ( 400, 10 ) )
        self.g_sizer.Add( ( 10, 10 ) )

        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

        wx.EVT_BUTTON( self, wc_path_browse_id, self.OnBrowseWorkingCopyDir )

    def loadState( self, state ):
        self.path_ctrl.SetValue( state.wc_path )

    def saveState( self, state ):
        # must get the abspath to convert c:/dir1/dir2 to c:\dir1\dir2
        # otherwise all sorts of things break inside workbench
        state.wc_path = os.path.abspath( os.path.expanduser( self.path_ctrl.GetValue().strip() ) )

        if not os.path.exists( state.wc_path ):
            wx.MessageBox( T_('Path %s\n'
                    'Does not exist\n'
                    'Choose an existing subversion working copy directory')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
            return False

        if not os.path.isdir( state.wc_path ):
            wx.MessageBox( T_('Path %s\n'
                    'Is not a directory\n'
                    'Choose an existing subversion working copy directory')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
            return False

        # handle the project name following solution
        project_name = state.project_name
        # replace project_name with the directory name
        state.project_name = state.wc_path.replace( '\\', '/' ).split( '/' )[-1]

        parts = state.project_name.split( '_' )
        # warn: if project name doesn't match the directory ...
        if len( parts ) > 1 and parts[1] != project_name:
            wx.MessageBox( T_('Preferred directory %s mismatches Project %s')
                    % ( state.wc_path, project_name ), style=wx.OK|wx.ICON_WARNING )

        if state.project_name in self.parent.pi_names:
            wx.MessageBox( T_('Project %s already exist.\n'
                    'Choose another name') % state.project_name,
                    style=wx.OK|wx.ICON_ERROR );
            return False

        return True

    def OnBrowseWorkingCopyDir( self, event ):
        filename = os.path.expanduser( self.path_ctrl.GetValue() )
        dir_dialog = wx.DirDialog(
            self,
            T_("Select project directory"),
            filename,
            style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON )

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.path_ctrl.SetValue( dir_dialog.GetPath() )

        dir_dialog.Destroy()

class WorkingCopyCreatePage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Create new Working Copy") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )


        self.wc_path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.wc_path_ctrl = wx.TextCtrl(self, wc_path_text_ctrl_id, '' )
        self.wc_path_browse = wx.Button( self, wc_path_browse_id, T_(" Browse... ") )

        self.g_sizer.Add( self.wc_path_label, 0, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.wc_path_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        self.g_sizer.Add( self.wc_path_browse, 0, wx.EXPAND )

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

        self.url_label = wx.StaticText( self, -1, T_('Subversion URL:'), style=wx.ALIGN_RIGHT )
        self.url_ctrl = wx.StaticText( self, -1, '' )

        self.g_sizer.Add( self.url_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.url_ctrl, 0, wx.EXPAND|wx.ALL, 5 )
        self.g_sizer.Add( (1, 1), 0, wx.EXPAND )
        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

        wx.EVT_BUTTON( self, wc_path_browse_id, self.OnBrowseWorkingCopyDir )


    def loadState( self, state ):
        self.wc_path_ctrl.SetValue( state.wc_path )
        self.url_ctrl.SetLabel( state.url_path )

    def saveState( self, state ):
        state.wc_path = os.path.expanduser( self.wc_path_ctrl.GetValue().strip() )
        if state.wc_path == '':
            wx.MessageBox( T_('Choose a directory that is empty and not in used by subversion'),
                    style=wx.OK|wx.ICON_ERROR );
            return False

        if os.path.exists( state.wc_path ):
            if not os.path.isdir( state.wc_path ):
                wx.MessageBox( T_('Path %s\n'
                        'Is not a directory\n'
                        'Choose a directory that is empty and not in use by subversion')
                        % state.wc_path, style=wx.OK|wx.ICON_ERROR );
                return False

            try:
                info = self.parent.client_pi.client_fg.info( state.wc_path )
                wx.MessageBox( T_('Path %s\n'
                    'Is a subversion working copy\n'
                    'Choose a directory that is empty and not in use by subversion')
                    % state.wc_path, style=wx.OK|wx.ICON_ERROR );
                return False
            except pysvn.ClientError:
                pass


            try:
                dir_list = os.listdir( state.wc_path )
                if len(dir_list) > 0:
                    wx.MessageBox(
                        T_('Path %s\n'
                            'Is not an empty directory\n'
                            'Choose a directory that is empty and not in use by subversion') %
                                state.wc_path,
                        style=wx.OK|wx.ICON_ERROR );
                    return False

            except (OSError,IOError), e:
                wx.MessageBox(
                    T_('Path %(path)s\n'
                        '%(error)s\n'
                        'Choose a directory that is empty and not in use by subversion') %
                        {'path': state.wc_path
                        ,'error': str(e)},
                    style=wx.OK|wx.ICON_ERROR );
                return False

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

class ProjectNamePage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Project Name") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )


        self.name_label = wx.StaticText(self, -1, T_('Project name:'), style=wx.ALIGN_RIGHT )
        self.name_ctrl = wx.TextCtrl(self, -1, '' )

        self.g_sizer.Add( self.name_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.name_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        self.g_sizer.Add( (1,1), 0, wx.EXPAND )

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

        self.wc_path_label = wx.StaticText(self, -1, T_('Working copy Path:'), style=wx.ALIGN_RIGHT )
        self.wc_path_ctrl = wx.StaticText(self, -1, '' )

        self.g_sizer.Add( self.wc_path_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.wc_path_ctrl, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL , 5 )
        self.g_sizer.Add( (1,1), 0, wx.EXPAND )

        self.url_label = wx.StaticText( self, -1, T_('Subversion URL:'), style=wx.ALIGN_RIGHT )
        self.url_ctrl = wx.StaticText( self, -1, '' )

        self.g_sizer.Add( self.url_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.url_ctrl, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
        self.g_sizer.Add( (1, 1), 0, wx.EXPAND )

        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

    def loadState( self, state ):
        self.wc_path_ctrl.SetLabel( state.wc_path )
        self.url_ctrl.SetLabel( state.url_path )

        if state.manifest:
            project_name = state.wc_path.replace( '\\', '/' ).split( '/' )[-1]
            self.name_ctrl.SetValue( project_name )
            # set prompt for url
            self.url_ctrl.SetLabel( T_('<Torun configspec set>') )

    def saveState( self, state ):
        state.project_name = self.name_ctrl.GetValue().strip()

        if state.project_name == '':
            wx.MessageBox( T_('Project name is blank.\n'
                    'Enter a project name'),
                    style=wx.OK|wx.ICON_ERROR );
            return False

        if state.project_name in self.parent.pi_names:
            wx.MessageBox( T_('Project %s already exist.\n'
                    'Choose another name') % state.project_name,
                    style=wx.OK|wx.ICON_ERROR );
            return False

        return True

    def GetNext( self ):
        return None

