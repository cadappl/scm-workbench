'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_app.py

'''
import sys
import os
import types
import logging
import threading
import inspect
import gettext
import locale

import wx
import wx.lib
import wx.lib.newevent


def checkTranslate(msg):
    print "Warning: Switch translation of <%s> to U_!" % msg
    return msg

def noTranslate(msg):
    return msg

import __builtin__
__builtin__.__dict__['T_'] = checkTranslate
__builtin__.__dict__['U_'] = noTranslate

import wb_frame
import wb_preferences
import wb_platform_specific
import wb_exceptions
import wb_diff_frame
import wb_dialogs
import wb_background_thread
import wb_shell_commands
import wb_repo_browser_frame
import wb_subversion_report_revision_changes
import wb_subversion_utils

# 2.8 has the convenient ACCEL_CMD
# on 2.6 we can add the feature
try: 
    wx.ACCEL_CMD
except AttributeError:
    if 'wxMac' in wx.PlatformInfo:
        wx.ACCEL_CMD = wx.ACCEL_ALT
    else:
        wx.ACCEL_CMD = wx.ACCEL_CTRL

AppCallBackEvent, EVT_APP_CALLBACK = wx.lib.newevent.NewEvent()

class WbApp(wx.App):
    def __init__( self, startup_dir, args ):
        # Debug settings

        # don't redirect IO into the log window
        self.__debug_noredirect = '--noredirect' in args

        # enable debug messages
        self.__debug = '--debug' in args
        self.__trace = '--trace' in args

        self.__last_client_error = []

        self.args = args
        self.app_name = os.path.basename( args[0] )
        self.app_dir = os.path.dirname( args[0] )
        if self.app_dir == '':
            self.app_dir = startup_dir

        self.main_thread = threading.currentThread()

        self.progress_format = None
        self.progress_values = {}

        wb_platform_specific.setupPlatform()

        self.setupLogging()
        self.log.info( T_('Work Bench starting') )

        # init the locale
        self.initLocale()

        if sys.platform == 'win32':
            languages = [locale.getdefaultlocale()[0]]
        else:
            languages = [locale.getlocale()[0]]

        locale_path = wb_platform_specific.getLocalePath( self )

        all_mofiles = gettext.find( 
                'pysvn_workbench',
                locale_path,
                languages,
                all=1 )

        self.translation = gettext.translation(
                'pysvn_workbench',
                locale_path,
                languages,
                fallback=True )

        __builtin__.__dict__['T_'] = self.translation.ugettext
        __builtin__.__dict__['S_'] = self.translation.ungettext
        # U_ is defined above for pre translation markup

        # --project <dir> automatically creates a project entry for <dir>
        # if <dir> is a subversion working copy and no project entry exists for it.
        self.auto_project_dir = None
        if '--project' in args:
            project_arg_index = args.index( '--project' )
            if project_arg_index < len( args ) - 1:
               self.auto_project_dir = os.path.abspath( os.path.join( startup_dir, args[ project_arg_index+1 ] ) )

        # debug output for locale issue debugging
        self.log.info( 'app_name %s' % (self.app_name,) )
        self.log.info( 'app_dir %s' % (self.app_dir,) )
        self.log.info( 'locale set to %r' % (locale.getlocale(),) )
        self.log.info( 'locale_path %s' % (locale_path) )
        self.log.info( 'languages %s' % (languages,) )
        self.log.info( 'find %r' % (gettext.find( 'pysvn_workbench', locale_path, languages, all=1 ),) )
        self.log.info( 'info %r' % (self.translation.info(),) )

        self.log.info( T_('PySVN WorkBench') )

        if '--test' in args:
            self.prefs = wb_preferences.Preferences(
                    self,
                    wb_platform_specific.getPreferencesFilename() + '.test',
                    wb_platform_specific.getOldPreferencesFilename() + '.test' )
        else:
            self.prefs = wb_preferences.Preferences(
                    self,
                    wb_platform_specific.getPreferencesFilename(),
                    wb_platform_specific.getOldPreferencesFilename() )

        self.lock_ui = 0
        self.need_activate_app_action = False

        self.frame = None
        self.all_diff_frames = []
        self.all_temp_files = []

        self.__paste_data = None

        self.background_thread = wb_background_thread.BackgroundThread()
        self.background_thread.start()

        wx.App.__init__( self, 0 )

        try_wrapper = wb_exceptions.TryWrapperFactory( self.log )

        wx.EVT_ACTIVATE_APP( self, try_wrapper( self.OnActivateApp ) )
        EVT_APP_CALLBACK( self, try_wrapper( self.OnAppCallBack ) )

    def isStdIoRedirect( self ):
        return not self.__debug_noredirect

    def eventWrapper( self, function ):
        return EventScheduling( self, function )

    def isMainThread( self ):
        'return true if the caller is running on the main thread'
        return self.main_thread is threading.currentThread()

    # codes determined by:
    # 1. System Preferences...
    # 2. Language and Text
    # 3. Drag lang to the top of the list
    # 4. look in ~/.CFUserTextEncoding
    _all_mac_locales = {
        '0:0':  'en_GB.utf-8',
        '0:3':  'de_DE.utf-8',
        }

    def initLocale( self ):
        self.log.info( 'initLocale ----------------------------------------' )
        # init the locale

        if sys.platform == 'win32':
            self.log.info( 'setlocale for windows' )
            # on windows this will set to the default
            locale.setlocale( locale.LC_ALL, '' )
            return

        if sys.platform == 'darwin':
            # on Mac this will set to the default
            # note: cannot find any docs on this to confirm its supported
            if '__CF_USER_TEXT_ENCODING' in os.environ:
                self.log.info( 'setlocale from __CF_USER_TEXT_ENCODING %s' % os.environ['__CF_USER_TEXT_ENCODING'] )
                lang_code = os.environ['__CF_USER_TEXT_ENCODING'].split( ':', 1 )[1]
                locale.setlocale( locale.LC_ALL, self._all_mac_locales.get( lang_code, '0:0' ) )
                return

        # generic Posix locale code
        if 'LC_ALL' in os.environ:
            try:
                self.log.info( 'setlocale from LC_ALL %s' % os.environ['LC_ALL'] )
                locale.setlocale( locale.LC_ALL, os.environ['LC_ALL'] )
                return

            except locale.Error, e:
                self.log.info( 'setlocale LC_ALL failed - %r' % (e,) )
                pass

        else:
            self.log.info( 'LC_ALL is not set' )
            for name in sorted( os.environ.keys() ):
                self.log.info( 'Env %s=%s' % (name, os.environ[ name ]) )

        language_code, encoding = locale.getdefaultlocale()
        self.log.info( 'getdefaultlocale -> %s, %s' % (language_code, encoding) )
        if language_code is None:
            language_code = 'en_US'

        if encoding is None:
            encoding = 'UTF-8'
        if encoding.lower() == 'utf':
            encoding = 'UTF-8'


        try:
            # setlocale fails when params it does not understand are passed
            self.log.info( 'setlocale language_code, encoding -> %s, %s' % (language_code, encoding) )
            locale.setlocale( locale.LC_ALL, '%s.%s' % (language_code, encoding) )

        except locale.Error, e:
            self.log.info( 'setlocale language_code - %r' % (e,) )

            try:
                # force a locale that will work
                self.log.info( 'setlocale set to en_US.UTF-8' )
                locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

            except locale.Error, e:
                self.log.info( 'setlocale set to en_US.UTF-8 - %r' % (e,) )
                locale.setlocale( locale.LC_ALL, 'C' )

    def setupLogging( self ):
        self.log = logging.getLogger( 'WorkBench' )
        self.trace = logging.getLogger( 'WorkBench.Trace' )

        if self.__debug:
            self.log.setLevel( logging.DEBUG )
        else:
            self.log.setLevel( logging.INFO )

        if self.__trace:
            self.trace.setLevel( logging.INFO )
        else:
            self.trace.setLevel( logging.CRITICAL )

        log_filename = wb_platform_specific.getLogFilename()
        # keep 10 logs of 100K each
        handler = RotatingFileHandler( log_filename, 'a', 100*1024, 10 )
        formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
        handler.setFormatter( formatter )
        self.log.addHandler( handler )

        if not self.isStdIoRedirect():
            handler = StdoutLogHandler()
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.log.addHandler( handler )

            handler = StdoutLogHandler()
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.trace.addHandler( handler )

        self.log.debug( 'debug enabled' )
        self.trace.info( 'trace enabled' )

    def log_client_error( self, e, title='Error' ):
        # must run on the main thread
        if not self.isMainThread():
            self.foregroundProcess( self.log_client_error, (e, title) )
            return

        self.__last_client_error = []
        try:
            for message, _ in e.args[1]:
                self.__last_client_error.append( message )
                self.log.error( message )

            wx.MessageBox( '\n'.join( self.__last_client_error ), title, style=wx.OK|wx.ICON_ERROR );
        except:
            pass

    def log_error( self, e, title='Error' ):
        # must run on the main thread
        if not self.isMainThread():
            self.foregroundProcess( self.log_error, (e, title) )
            return

        message = str( e )
        self.log.error( message )

        wx.MessageBox( message, title, style=wx.OK|wx.ICON_ERROR );

    def refreshFrame( self ):
        self.frame.refreshFrame()

    def expandSelectedTreeNode( self ):
        self.frame.expandSelectedTreeNode()

    def selectTreeNodeInParent( self, filename ):
        self.frame.selectTreeNodeInParent( filename )

    def selectTreeNode( self, filename ):
        self.frame.selectTreeNode( filename )

    def setAction( self, msg ):
        self.frame.setAction( msg )

    def setProgress( self, fmt, total ):
        self.progress_format = fmt
        self.progress_values['total'] = total
        self.progress_values['count'] = 0
        self.progress_values['percent'] = 0
        self.frame.setProgress( self.progress_format % self.progress_values )

    def incProgress( self ):
        if self.progress_format is None:
            return
        self.progress_values['count'] += 1
        if self.progress_values['total'] > 0:
            self.progress_values['percent'] = self.progress_values['count']*100/self.progress_values['total']
        self.frame.setProgress( self.progress_format % self.progress_values )

    def getProgressValue( self, name ):
        return self.progress_values[ name ]

    def clearProgress( self ):
        self.progress_format = None
        self.frame.setProgress( '' )

    def setPasteData( self, data ):
        self.__paste_data = data

    def clearPasteData( self ):
        self.__paste_data = None

    def hasPasteData( self ):
        return self.__paste_data is not None

    def getPasteData( self ):
        return self.__paste_data

    # called from wb_subversion_history to avoid circular imports
    def showReportRevisionChangesFrame( self, project_info, changed_files, info1, info2 ):
        revision_changes_frame = wb_subversion_report_revision_changes.ReportRevisionChangesFrame(
                                    self, project_info,
                                    changed_files, info1, info2 )
        revision_changes_frame.Show( True )


    def diffFiles( self, file_left, title_left, file_right, title_right ):
        diff_frame = wb_diff_frame.DiffFrame(
            self, self.frame,
            file_left, title_left,
            file_right, title_right )
        # only show if the files could be read
        if diff_frame.isOk():
            diff_frame.showAllFolds( False )
            diff_frame.Show( True )

            self.all_diff_frames.append( diff_frame )

    def DiffDone( self, diff_frame ):
        self.all_diff_frames.remove( diff_frame )

    def confirmAction( self, title, all_filenames ):
        dialog = wb_dialogs.ConfirmAction( self.frame, title, all_filenames )
        result = dialog.ShowModal()
        return result == wx.ID_OK

    def confirmForceAction( self, title, all_filenames ):
        dialog = wb_dialogs.ConfirmAction( self.frame, title, all_filenames, force_field=True )
        result = dialog.ShowModal()
        return result == wx.ID_OK, dialog.getForce()

    def getLogMessage( self, title, all_filenames ):
        dialog = wb_dialogs.LogMessage( self.frame, title, all_filenames,
                                        wb_platform_specific.getLastCheckinMessageFilename() )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return True, dialog.getLogMessage()
        return False, ''

    def getLockMessage( self, title, all_filenames ):
        dialog = wb_dialogs.LogMessage( self.frame, title, all_filenames,
                                        wb_platform_specific.getLastLockMessageFilename(), force_field=True )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return dialog.getLogMessage(), dialog.getForce()
        return None, False

    def addFile( self, title, name, force=None ):
        dialog = wb_dialogs.AddDialog( self.frame, title, name, force )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return dialog.getForce()
        return None

    def addFolder( self, title, name, force, recursive=None ):
        dialog = wb_dialogs.AddDialog( self.frame, title, name, force, recursive=recursive )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return dialog.getForce(), dialog.getRecursive()

        return None, None


    def renameFile( self, title, old_name, force=None ):
        dialog = wb_dialogs.RenameFile( self.frame, title, old_name, force )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return dialog.getNewFilename(), dialog.getForce()
        return None, None

    def getCredentials( self, realm, username, may_save ):
        # signature allows use a pysvn callback
        dialog = wb_dialogs.GetCredentials( self.frame, realm, username, may_save )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return (True, dialog.getUsername().encode('UTF-8'),
                dialog.getPassword().encode('UTF-8'), dialog.getSaveCredentials())
        else:
            return False, '', '', False

    def getServerTrust( self, realm, info_list, may_save ):
        # signature allows use a pysvn callback
        dialog = wb_dialogs.GetServerTrust( self.frame, realm, info_list, may_save )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            # Trust, save
            return True, dialog.getSaveTrust()
        else:
            # don't trust, don't save
            return False, False

    def getFilename( self, title, border_title ):
        dialog = wb_dialogs.GetFilename( self.frame, title, border_title )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return True, dialog.getNewFilename()
        else:
            return False, ''

    def getIdent( self, title, dir_name, ban_list, no_name=False ):
        dialog = wb_dialogs.NewIdent( self.frame, title, dir_name, ban_list, no_name )
        result = dialog.ShowModal()

        if no_name:
            if result == wx.ID_OK:
                return True, dialog.getTagName()
            else:
                return False, ''
        else:
            if result == wx.ID_OK:
                return True, dialog.getDirName(), dialog.getTagName()
            else:
                return False, '', ''

    def getRepositoryPath( self, parent, url='' ):
        dialog = wb_repo_browser_frame.RepoBrowserDialog( parent, self, url )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            return dialog.getUrl()
        else:
            return ''

    def savePreferences( self ):
        self.prefs.writePreferences()

    def exitAppNow( self ):
        if self.lock_ui > 0:
            # return False to veto a close
            return False

        # o.k. to exit
        for temp_file in self.all_temp_files:
            self.log.info( 'Removing "%s".' % temp_file )
            try:
                os.remove( temp_file )
            except OSError:
                pass

        self.frame.savePreferences()
        self.prefs.writePreferences()
        self.frame = None

        return True

    def OnInit(self):
        self.frame = wb_frame.WbFrame( self )
        self.frame.Show( True )
        self.SetTopWindow( self.frame )

        self.foregroundProcess( self.frame.tree_panel.initFrame, () )
        return True

    def OnActivateApp( self, event ):
        if self.frame is None:
            # too early or too late
            return

        if self.lock_ui == 0:
            self.frame.OnActivateApp( event.GetActive() )
        else:
            if event.GetActive():
                self.need_activate_app_action = True

    def backgroundProcess( self, function, args ):
        self.background_thread.addWork( AppBackgroundFunction( self, function, args ) )

    def foregroundProcess( self, function, args ):
        wx.PostEvent( self, AppCallBackEvent( callback=function, args=args ) )

    def OnAppCallBack( self, event ):
        try:
            event.callback( *event.args )
        except:
            self.log.exception( 'OnAppCallBack<%s.%s>\n' %
                (event.callback.__module__, event.callback.__name__ ) )

    def debugShowCallers( self, depth ):
        if not self.__debug:
            return

        stack = inspect.stack()
        for index in range( 1, depth+1 ):
            if index >= len(stack):
                break

            caller = stack[ index ]
            filename = os.path.basename( caller[1] )
            self.log.debug( 'File: %s:%d, Function: %s' % (filename, caller[2], caller[3]) )
            del caller

        del stack

class AppBackgroundFunction:
    def __init__( self, app, function, args ):
        self.app = app
        self.function = function
        self.args = args

    def __call__( self ):
        self.app.trace.info( 'AppBackgroundFunction<%s.%s>.__call__()' %
                (self.function.__module__, self.function.__name__) )
        try:
            self.function( *self.args )
        except:
            self.app.log.exception( 'AppBackgroundFunction<%s.%s>\n' %
                (self.function.__module__, self.function.__name__) )

class EventScheduling:
    def __init__( self, app, function ):
        self.app = app
        self.function = function

    def __call__( self, *args, **kwds ):
        self.app.trace.info( 'EventScheduling<%s.%s>.__call__()' %
                (self.function.__module__, self.function.__name__) )
        try:
            # call the function
            result = self.function( *args, **kwds )

            # did the function run or make a generator?
            if type(result) != types.GeneratorType:
                # it ran - we are all done
                return

            # step the generator
            stepGenerator( self.app, result )
        except:
            self.app.log.exception( 'EventScheduling<%s.%s>\n' %
                (self.function.__module__, self.function.__name__ ) )

def stepGenerator( app, generator ):
    app.trace.info( 'stepGenerator<%r>() next_fn=%r' % (generator, generator.next) )

    # result tells where to schedule the generator to next
    try:
        where_to_go_next = generator.next()
        app.trace.info( 'stepGenerator<%r>() next=>%r' % (generator, where_to_go_next) )

    except StopIteration:
        # no problem all done
        return

    # will be one of app.foregroundProcess or app.backgroundProcess
    where_to_go_next( stepGenerator, (app, generator) )

#--------------------------------------------------------------------------------
#
#    RotatingFileHandler - based on python lib class
#
#--------------------------------------------------------------------------------
class RotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0):
        """
        Open the specified file and use it as the stream for logging.

        By default, the file grows indefinitely. You can specify particular
        values of maxBytes and backupCount to allow the file to rollover at
        a predetermined size.

        Rollover occurs whenever the current log file is nearly maxBytes in
        length. If backupCount is >= 1, the system will successively create
        new files with the same pathname as the base file, but with extensions
        ".1", ".2" etc. appended to it. For example, with a backupCount of 5
        and a base file name of "app.log", you would get "app.log",
        "app.log.1", "app.log.2", ... through to "app.log.5". The file being
        written to is always "app.log" - when it gets filled up, it is closed
        and renamed to "app.log.1", and if files "app.log.1", "app.log.2" etc.
        exist, then they are renamed to "app.log.2", "app.log.3" etc.
        respectively.

        If maxBytes is zero, rollover never occurs.
        """
        logging.FileHandler.__init__(self, filename, mode)
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        if maxBytes > 0:
            self.mode = "a"

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """

        self.stream.close()
        if self.backupCount > 0:
            prefix, suffix = os.path.splitext( self.baseFilename )
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d%s" % (prefix, i, suffix)
                dfn = "%s.%d%s" % (prefix, i+1, suffix)
                if os.path.exists(sfn):
                    #print "%s -> %s" % (sfn, dfn)
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
            #print "%s -> %s" % (self.baseFilename, dfn)
        self.stream = open(self.baseFilename, "w")

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in setRollover().
        """
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            try:
                self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
                if self.stream.tell() + len(msg) >= self.maxBytes:
                    self.doRollover()

            except ValueError:
                # on Windows we get "ValueError: I/O operation on closed file"
                # when a second copy of workbench is run
                self.doRollover()

        logging.FileHandler.emit(self, record)

class StdoutLogHandler(logging.Handler):
    def __init__( self ):
        logging.Handler.__init__( self )

    def emit( self, record ):
        try:
            msg = self.format(record) + '\n'

            sys.__stdout__.write( msg )

        except:
            self.handleError(record)

#- QQQ -------------------------------------------------------------------------------
# Locate a .mo file using the gettext strategy
def find(log, domain, localedir=None, languages=None, all=0):
    log.info( 'find( %r, %r, %r, %r )' % (domain, localedir, languages, all) )

    # Get some reasonable defaults for arguments that were not supplied
    if localedir is None:
        localedir = _default_localedir
    if languages is None:
        languages = []
        for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(envar)
            if val:
                languages = val.split(':')
                break
        if 'C' not in languages:
            languages.append('C')
    # now normalize and expand the languages
    nelangs = []
    for lang in languages:
        for nelang in _expand_lang(log, lang):
            if nelang not in nelangs:
                nelangs.append(nelang)
    # select a language
    if all:
        result = []
    else:
        result = None

    log.info( 'find: nelangs %r' % (nelangs,) )

    for lang in nelangs:
        if lang == 'C':
            break
        mofile = os.path.join(localedir, lang, 'LC_MESSAGES', '%s.mo' % domain)
        log.info( 'find: mofile %r' % (mofile,) )
        if os.path.exists(mofile):
            if all:
                result.append(mofile)
            else:
                return mofile
    return result

def _expand_lang(log, locale):
    from locale import normalize
    locale = normalize(locale)
    COMPONENT_CODESET   = 1 << 0
    COMPONENT_TERRITORY = 1 << 1
    COMPONENT_MODIFIER  = 1 << 2
    # split up the locale into its base components
    mask = 0
    pos = locale.find('@')
    if pos >= 0:
        modifier = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_MODIFIER
    else:
        modifier = ''
    pos = locale.find('.')
    if pos >= 0:
        codeset = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_CODESET
    else:
        codeset = ''
    pos = locale.find('_')
    if pos >= 0:
        territory = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_TERRITORY
    else:
        territory = ''
    language = locale
    ret = []
    for i in range(mask+1):
        if not (i & ~mask):  # if all components for this combo exist ...
            val = language
            if i & COMPONENT_TERRITORY: val += territory
            if i & COMPONENT_CODESET:   val += codeset
            if i & COMPONENT_MODIFIER:  val += modifier
            ret.append(val)
    ret.reverse()
    return ret



