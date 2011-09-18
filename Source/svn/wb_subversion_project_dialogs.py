'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010-2011 ccc. All right reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_project_dialogs.py

'''
import wx
import wx.wizard
import wb_source_control_providers
import pysvn
import os

import wb_config

import wb_read_file

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

class AddProjectDialog:
    def __init__( self, app, parent ):
        self.app = app

        provider = wb_source_control_providers.getProvider( 'subversion' )
        pi = provider.getProjectInfo( self.app )

        pi.init( '', wc_path='', url='' )
        self.client_pi = pi

        # get the list of names to use in the validation
        pi_list = self.app.prefs.getProjects().getProjectList()
        self.pi_names = [pi.project_name for pi in pi_list]

        self.wizard = wx.wizard.Wizard( parent, wizard_id, T_("Add subversion Project") )

        self.page_wc_choice = WorkingCopyChoicePage( self )
        self.page_wc_exists = WorkingCopyExistsPage( self )
        self.page_url = SubversionUrlPage( self )
        self.page_wc_create = WorkingCopyCreatePage( self )

        self.page_project_name = ProjectNamePage( self )

        self.page_wc_choice.SetNext( self.page_project_name )

        self.page_wc_exists.SetPrev( self.page_wc_choice )
        self.page_wc_exists.SetNext( self.page_project_name )

        self.page_url.SetPrev( self.page_wc_choice )
        self.page_url.SetNext( self.page_wc_create )

        self.page_wc_create.SetPrev( self.page_url )
        self.page_wc_create.SetNext( self.page_project_name )

        self.page_project_name.SetPrev( self.page_wc_create )

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
        provider = wb_source_control_providers.getProvider( 'subversion' )
        pi = provider.getProjectInfo( self.app )

        pi.init( self.state.project_name, wc_path=self.state.wc_path, url=self.state.url_path )

        return pi

    def OnPageChanged( self, event ):
        page = event.GetPage()
        page.loadState( self.state )

    def OnPageChanging( self, event ):
        page = event.GetPage()
        if event.GetDirection():
            if not page.saveState( self.state ):
                event.Veto()


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

        self.sizer.Add( (10, 50) )
        self.sizer.Add( self.radio_new, 0, wx.ALL, 5 )
        self.sizer.Add( (5, 5) )
        self.sizer.Add( self.radio_existing, 0, wx.ALL, 5 )

    def GetNext( self ):
        if self.radio_existing.GetValue():
            return self.parent.page_wc_exists
        if self.radio_new.GetValue():
            return self.parent.page_url
        return None

    def loadState( self, state ):
        self.radio_existing.SetValue( state.use_existing )
        self.radio_new.SetValue( not state.use_existing )

    def saveState( self, state ):
        state.use_existing = self.radio_existing.GetValue()
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

