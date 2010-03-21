'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

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

class ProjectDialog(wx.Dialog):
    def __init__( self, app, parent, title ):
        wx.Dialog.__init__( self, parent, -1, title )

        self.app = app
        self.client = pysvn.Client()
        self.client.exception_style = 1

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
        provider = wb_source_control_providers.getProvider( 'subversion' )
        pi = provider.getProjectInfo( self.app )
        pi.new_file_template_dir = self.newfile_dir_ctrl.GetValue().strip()

        pi.init( self.name_ctrl.GetValue().strip(),
            wc_path=os.path.expanduser( self.wc_path_ctrl.GetValue().strip() ),
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

class AddProjectState:
    def __init__( self ):
        self.use_existing = False
        self.wc_path = ''
        self.url_path = ''
        self.project_name = ''

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

        self.wizard = wx.wizard.Wizard( parent, wizard_id, T_("Add Project") )

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

        self.state = AddProjectState()

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

