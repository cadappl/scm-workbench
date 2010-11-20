'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_project_dialogs.py

'''
import wx
import wx.wizard
import wb_torun_configspec
import wb_source_control_providers
import pysvn
import os

#
#    Later need to make these dialogs work with the
#    registered providers to put up provider specific
#    dialog.
#
wc_path_browse_id = wx.NewId()
wc_path_text_ctrl_id = wx.NewId()
name_text_ctrl_id = wx.NewId()
url_trunk_path_text_ctrl_id = wx.NewId()
url_tags_path_text_ctrl_id = wx.NewId()

wizard_id = wx.NewId()

#FIXME: share the font definition in wb_diff_frame
import wb_diff_frame

class _TinyEditor(wx.Dialog):
    def __init__(self, parent, title, text=''):
        wx.Dialog.__init__(self, parent, -1, title,
          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.FIXED_MINSIZE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.textctrl = wx.TextCtrl(self, -1, text,
                        size=(500, 400),
                        style=wx.HSCROLL|wx.TE_MULTILINE|wx.TE_RICH2)
        # FIXME: fix the referrence in wb_diff_frame
        self.textctrl.SetFont(wx.Font(wb_diff_frame.point_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, wb_diff_frame.face))
        sizer.Add(self.textctrl, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(wx.StaticLine(self, -1, size=(20,-1),
                  style=wx.LI_HORIZONTAL),
                  0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_BOTTOM|wx.ALL, 5)
        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL),
                  0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)

        self.SetSizer(sizer)
        self.Fit()

    def GetValue( self ):
        return self.textctrl.GetValue()

class AddProjectState:
    def __init__( self ):
        self.use_existing = False
        self.wc_path = ''
        self.url_path = ''
        self.project_name = ''
        self.configspec = ''

class AddProjectDialog:
    def __init__( self, app, parent ):
        self.app = app
        self.provider_name = ''

        # get the list of names to use in the validation
        pi_list = self.app.prefs.getProjects().getProjectList()
        self.pi_names = [pi.project_name for pi in pi_list]

        self.wizard = wx.wizard.Wizard( parent, wizard_id, T_("Add Project") )

        self.page_wc_choice = WorkingCopyChoicePage( self )
        self.page_wc_exists = WorkingCopyExistsPage( self )
        self.page_url = SubversionUrlPage( self )
        self.page_wc_create = WorkingCopyCreatePage( self )

        self.page_project_name = ProjectNamePage( self )
        self.page_cs_choice = TorunProjectSelectionPage( self )
        self.page_directory = DirectoryPage( self )

        self.page_wc_choice.SetNext( self.page_project_name )

        self.page_wc_exists.SetPrev( self.page_wc_choice )
        self.page_wc_exists.SetNext( self.page_project_name )

        self.page_url.SetPrev( self.page_wc_choice )
        self.page_url.SetNext( self.page_wc_create )

        self.page_wc_create.SetPrev( self.page_url )
        self.page_wc_create.SetNext( self.page_project_name )

        self.page_project_name.SetPrev( self.page_wc_create )

        self.wizard.FitToPage( self.page_wc_exists )

        self.page_cs_choice.SetPrev( self.page_wc_choice )
        self.page_cs_choice.SetNext( self.page_directory )
        self.page_directory.SetPrev( self.page_cs_choice )
        self.wizard.Bind( wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged )
        self.wizard.Bind( wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging )

        self.state = AddProjectState()

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
                 configspec=self.state.configspec,
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
        self.radio_new = wx.RadioButton( self, -1, T_(" Use new working copy directory "), style = wx.RB_GROUP )
        self.radio_existing = wx.RadioButton( self, -1, T_(" Use existing Working copy directory ") )

        self.radio_torun = wx.RadioButton( self, -1, T_(" Create Torun project with working directory ") )
        self.sizer.Add( (10, 50) )
        self.sizer.Add( self.radio_new, 0, wx.ALL, 5 )
        self.sizer.Add( (5, 5) )
        self.sizer.Add( self.radio_existing, 0, wx.ALL, 5 )
        self.sizer.Add( (5, 5))
        self.sizer.Add( self.radio_torun, 0, wx.ALL, 5)

    def GetNext( self ):
        if self.radio_existing.GetValue():
            return self.parent.page_wc_exists
        if self.radio_new.GetValue():
            return self.parent.page_url
        if self.radio_torun.GetValue():
            return self.parent.page_cs_choice
        return None

    def loadState( self, state ):
        self.radio_new.SetValue( state.use_existing == 0 )
        self.radio_existing.SetValue( state.use_existing == 1 )
        self.radio_torun.SetValue( state.use_existing == 2 )

    def saveState( self, state ):
        if self.radio_new.GetValue():
            state.use_existing = 0
        elif self.radio_existing.GetValue():
            state.use_existing = 1
        elif self.radio_torun.GetValue():
            state.use_existing = 2

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

        self._update_controls_lock = False

    def loadState( self, state ):
        self.wc_path_ctrl.SetValue( state.wc_path )
        self.updateControls()

    def saveState( self, state ):
        self.parent.setProviderName( 'subversion' )
        # must get the abspath to convert c:/dir1/dir2 to c:\dir1\dir2
        # otherwise all sorts of things break inside workbench
        state.wc_path = os.path.abspath( os.path.expanduser( self.wc_path_ctrl.GetValue().strip() ) )
        state.url_path = self.url_ctrl.GetLabel().strip()

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

        if state.url_path == '':
            wx.MessageBox( T_('Path %s\n'
                    'Is not a subversion working copy\n'
                    'Choose an existing subversion working copy directory')
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

        # If the wc_path exists and is a svn wc then disable the url field
        wc_path = self.wc_path_ctrl.GetValue()
        wc_path = os.path.expanduser( wc_path )

        url = None
        if os.path.exists( wc_path ):
            try:
                info = self.parent.client_pi.client_fg.info( wc_path )
                url = info.url
            except pysvn.ClientError:
                pass

        if url is None:
            self.url_ctrl.SetLabel( '' )
        else:
            self.url_ctrl.SetLabel( url )

        self._update_controls_lock = False


class SubversionUrlPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Subversion URL") )

        self.g_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.g_sizer.AddGrowableCol( 1 )


        self.url_path_label = wx.StaticText(self, -1, T_('Subversion URL:'), style=wx.ALIGN_RIGHT )
        self.url_path_ctrl = wx.TextCtrl(self, url_trunk_path_text_ctrl_id, '' )

        self.g_sizer.Add( self.url_path_label, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5 )
        self.g_sizer.Add( self.url_path_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        self.g_sizer.Add( (1, 1), 0, wx.EXPAND )

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

        self.sizer.Add( self.g_sizer, 0, wx.ALL, 5 )

    def loadState( self, state ):
        self.url_path_ctrl.SetValue( state.wc_path )

    def saveState( self, state ):
        self.parent.setProviderName( 'subversion' )
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

class TorunProjectSelectionPage(TitledPage):
    def __init__( self, parent ):
        TitledPage.__init__( self, parent, T_("Select Configspec") )

        self.configspec = ''
        self.repo_list = None

        self.client = pysvn.Client()
        self.client.exception_style = 1

        # choose for creation type
        typeList = ['Create with Configspec', 'Create with Baseline info']
        type_box = wx.RadioBox( self, -1, "Creation Type", wx.DefaultPosition,
                          wx.DefaultSize, typeList, 2, wx.RA_SPECIFY_COLS )

        type_box.Bind( wx.EVT_RADIOBOX, self.OnChangeConfigspecCategory)

        self.label_id = wx.StaticBox( self, -1, T_("Project ID") )
        self.project_id = wx.ComboBox( self, -1, style=wx.CB_READONLY|wx.CB_SORT )
        self.label_lbl = wx.StaticBox( self, -1, T_("Project Label") )
        self.project_label = wx.ComboBox( self, -1, style=wx.CB_READONLY|wx.CB_SORT )
        self.extend_proj = wx.CheckBox( self, -1, T_("Include Extended Projects") )

        sb = wx.StaticBox( self, -1, T_( "Baseline Info" ) )
        info_sizer = wx.StaticBoxSizer( sb, wx.VERTICAL )
        prj_size = wx.FlexGridSizer( 0, 4, 2, 2 )
        prj_size.AddGrowableCol( 1 )
        prj_size.AddGrowableCol( 3 )
        prj_size.AddMany([ ( self.label_id, 0 ),
                           ( self.project_id, 0, wx.EXPAND|wx.ALL ),
                           ( self.label_lbl, 0 ),
                           ( self.project_label, 0, wx.EXPAND|wx.ALL ) ])

        info_sizer.Add( prj_size, 0, wx.EXPAND|wx.ALL, 5 )
        info_sizer.Add( self.extend_proj, 0, wx.ALL, 5 )

        spec = wx.StaticBox( self, -1, T_("Configspec") )
        spec_sizer = wx.StaticBoxSizer( spec, wx.HORIZONTAL )
        spec_text = wx.StaticText( self, -1, T_("The configspec obeys the syntax of ClearCase Configspec") )
        self.spec_button = wx.Button( self, -1, T_("Configspec") )

        spec_sizer.Add( spec_text, 0, wx.EXPAND|wx.ALL, 5 )
        spec_sizer.Add( self.spec_button, 0, wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, 5 )

        self.sizer.Add( type_box, 0, wx.EXPAND|wx.ALL, 5 )
        self.sizer.Add( info_sizer, 0, wx.EXPAND|wx.ALL, 5 )
        self.sizer.Add( spec_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        self.extend_proj.Bind( wx.EVT_CHECKBOX, self.OnSelectExtendedProject )
        self.project_id.Bind( wx.EVT_COMBOBOX, self.OnProjectIdChange )
        self.project_label.Bind( wx.EVT_COMBOBOX, self.OnProjectLabelChange )
        self.spec_button.Bind( wx.EVT_BUTTON, self.OnConfigspecClick )

        self.updateControls(0)

    def loadState( self, state ):
        self.configspec = state.configspec

    def saveState( self, state ):
        self.parent.setProviderName( 'torun' )

        if self.configspec == '':
            wx.MessageBox( T_('Select a project with one specified version, or enter a configspec'),
                    style=wx.OK|wx.ICON_ERROR );
            return False

        configspec_parser = wb_torun_configspec.wb_subversion_configspec(self.configspec)
        if configspec_parser.error():
            wx.MessageBox( T_(configspec_parser.error() ), style=wx.OK|wx.ICON_ERROR )
            return False

        state.configspec = self.configspec
        state.project_name = self.project_id.GetClientData( self.project_id.GetSelection() )

        return True

    def OnChangeConfigspecCategory( self, event ):
        choice = event.GetInt()

        self.updateControls( choice )

    def OnSelectExtendedProject( self, event ):
        self.updateControls( self.choice )

    def OnProjectIdChange( self, event ):
        project = self.project_id.GetClientData( self.project_id.GetSelection() )
        if project == None:
            return

        uproject = project.upper()
        project_location = self.repo_list.get( project )
        if not project_location:
            return

        # FIXME: handle the prefix '/vobs'
        prefix = '/vobs/'
        dir_list = dict()

        repo_name = (project_location.split('/'))[2]
        repo_location = self.repo_map.get(repo_name)
        if not repo_location:
            return

        if not repo_location.endswith('/'):
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
                if item.name.rfind('/tags/%s-' % uproject) > 0:
                    label = item.name.split('/')[-1]
                    dir_list[ label ] = item.name
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
                if item.name.rfind( '/tags/%s/' % uproject ) > 0:
                    label = '%s-%s' % ( uproject, item.name.split('/')[-1] )
                    dir_list[ label ] = item.name
        except:
            # ignore the exception
            pass

        self.project_label.Clear()
        if len( dir_list ) > 0:
            for item in dir_list.keys():
                self.project_label.Append( item, dir_list[item] )

            self.project_label.SetSelection( 0 )
            self.OnProjectLabelChange( None )

    def OnProjectLabelChange( self, event ):
        location = self.project_label.GetClientData( self.project_label.GetSelection() )

        # read the configspec with the order defined in the list
        project = self.project_id.GetClientData( self.project_id.GetSelection() )

        for name in [ 'configspec', 'config_spec', 'configspec.linux',
                      'configspec.cygwin', 'configspec.windows' ]:
            try:
                url = '%s/%s/confm/%s' % ( location, project, name )
                text = self.client.cat(url,
                        revision=pysvn.Revision( pysvn.opt_revision_kind.head ),
                        peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified) )

                self.configspec = \
"""\
#====================================
# Generated from %s
#====================================

%s
#===+PROJECT
element %s/%s/... %s
""" % ( name, text, self.repo_list[project], project, self.project_label.GetValue() )

                break
            except:
                pass

    def OnConfigspecClick( self, event ):
        editor = _TinyEditor(self, 'Edit Configspec', self.configspec)
        if editor.ShowModal() == wx.ID_OK:
            self.configspec = editor.GetValue()
            editor.Destroy()

    def updateControls( self, choice ):
        self.choice = choice
        self.project_id.Enable( choice == 1 )
        self.project_label.Enable( choice == 1 )
        self.extend_proj.Enable( choice == 1 )

        if choice == 1:
            if not self.repo_list:
                p = self.parent.app.prefs.getRepository()
                self.repo_list = self._readRepoList( p.repo_baseline )
                self.repo_map = p.repo_map_list

            self.project_id.Clear()
            for item in self.repo_list.keys():
                if item.startswith( 'vy' ):
                    value = item.replace( 'vy', 'VY' )
                else:
                    value = item

                if self.extend_proj.IsChecked():
                    self.project_id.Append( value, item )
                # only the project leading with VY are standard SiG project
                elif value.startswith( 'VY' ):
                    self.project_id.Append( value, item )

            self.project_id.SetSelection( 0 )
            self.OnProjectIdChange( None )

    def _readRepoList( self, repo_url ):
        ret = dict()

        repo_url = repo_url.replace( '\\', '/' )
        if not repo_url.endswith( '/' ):
            repo_url += '/'

        text = None
        for suffix in ['trunk/' + (repo_url.split('/'))[-2] + '/repo.list',
                       'trunk/baseline/repo.list',
                       'trunk/repo.list',
                       'repo.list']:
            try:
                text = self.client.cat(repo_url + suffix,
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
                a = li.strip().replace( '\t', ' ' ).split( ' ' )
                if len(a) > 1:
                    ret[ a[0] ] = a[-1]

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

        self.g_sizer.Add( (10,10) )
        self.g_sizer.Add( (400,10) )
        self.g_sizer.Add( (10,10) )

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

        # handle the project name following SIG solution
        project_name = state.project_name
        # replace project_name with the directory name
        state.project_name = state.wc_path.replace( '\\', '/' ).split( '/' )[-1]

        parts = state.project_name.split( '_' )
        # warn: if project name doesn't match the directory ...
        if len( parts ) > 1 and parts[1] != project_name:
            wx.MessageBox( T_('Preferred directory %s mismatches Project %s')
                    % ( state.wc_path, state.project_name ), style=wx.OK|wx.ICON_WARNING )

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

