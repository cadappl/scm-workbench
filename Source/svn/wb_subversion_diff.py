'''
 ====================================================================
 Copyright (c) 2003-2007 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_diff.py

'''
import sys
import os
import tempfile

import pysvn

import wb_shell_commands
import wb_show_diff_frame
import wb_read_file
import wb_diff_frame

debug_diff = False

#
#   Hold the information about each path to be compared
#
class PathInfoForDiff:
    def __init__( self ):
        # peg_path and peg_revision of the starting point for this path
        self.peg_path = None
        self.peg_revision = None
        # path and revision to be compared found starting the peg
        self.path = None
        self.revision = None
        # title for the diff program
        self.title = None

    def copy( self ):
        path_info = PathInfoForDiff()

        path_info.peg_path = self.peg_path
        path_info.peg_revision = self.peg_revision
        path_info.path = self.path
        path_info.revision = self.revision
        path_info.title = self.title
        return path_info

    def pegIsEqual( self, path_info ):
        # is either is has None in the peg fields
        # say it does not match
        if( self.peg_revision is None
        or self.peg_path is None ):
            return False

        if( path_info.peg_revision is None
        or path_info.peg_path is None ):
            return False

        return (self.peg_path == path_info.peg_path
            and self.peg_revision == path_info.peg_revision)

    def printDescription( self, title ):
        print '%s PathInfoForDiff' % title
        print '      peg_path: %r' % self.peg_path
        print '  peg_revision: %r' % self.peg_revision
        print '          path: %r' % self.path
        print '      revision: %r' % self.revision
        print '         title: %r' % self.title

#
#   Diff two files using the mode selected by the user
#
#   The files can be on disk or at any revision
#

def subversionDiffFiles(
        app,
        project_info,
        old_path_info,
        new_path_info ):

    # if revision is None cannot ask svn for the contents
    mode = app.prefs.getDiffTool().diff_tool_mode
    app.log.debug( 'subversionDiffFiles: mode %r' % mode )

    # svn diff only works on versioned files
    if mode == 'svn-diff' and (old_path_info.revision is None or new_path_info.revision is None):
        mode = 'built-in'

    # Check for possible errors in advance to give the user a clear message.
    for path_info in (old_path_info, new_path_info):
        if( path_info.revision is None
        or path_info.revision.kind == pysvn.opt_revision_kind.working ):
            if not os.path.exists( path_info.path ):
                app.log_error( '"%s" does not exist.' % path_info.path )
                fd, path_info.path = tempfile.mkstemp( suffix=os.path.basename( path_info.path ) )
                os.close( fd )
                # keep track of the temp file
                app.all_temp_files.append( path_info.path )

            if os.path.isdir( path_info.path ):
                app.log_error( '"%s" refers to a directory.' % path_info.path )
                return

            if not os.access( path_info.path, os.R_OK ):
                app.log_error( '"%s" cannot be read.' % path_info.path )
                return

    if mode == 'svn-diff':
        # svn will do all the work
        yield app.backgroundProcess

        diff_text = project_info.client_bg.diff(
                tempfile.gettempdir(),
                old_path_info.path, old_path_info.revision,
                new_path_info.path, new_path_info.revision )

        yield app.foregroundProcess

        showDiffText( app, diff_text, old_path_info.title, new_path_info.title )

    elif mode == 'external-gui-diff':
        yield app.backgroundProcess

        ok = False
        try:
            old_temp_filename = __getLocalFilename( app, project_info, old_path_info )
            new_temp_filename = __getLocalFilename( app, project_info, new_path_info )

            ok = True

        except IOError, e:
            app.log_error( e )

        yield app.foregroundProcess

        if ok:
            wb_shell_commands.GuiDiffFiles( app,
                             __processExternalCommandOptions( app,
                                app.prefs.getDiffTool().gui_diff_tool_options[:],
                                old_temp_filename, old_path_info.title,
                                new_temp_filename, new_path_info.title ) )

    elif mode == 'external-shell-diff':
        yield app.backgroundProcess

        ok = False
        try:
            old_temp_filename = __getLocalFilename( app, project_info, old_path_info )
            new_temp_filename = __getLocalFilename( app, project_info, new_path_info )

            diff_text = wb_shell_commands.ShellDiffFiles( app,
                            __processExternalCommandOptions( app,
                                app.prefs.getDiffTool().shell_diff_tool_options[:],
                                old_temp_filename, old_path_info.title,
                                new_temp_filename, new_path_info.title ) )

            ok = True

        except IOError, e:
            app.log_error( e )

        yield app.foregroundProcess

        if ok:
            showDiffText( app, diff_text, old_path_info.title, new_path_info.title )
    else:
        ok = False
        yield app.backgroundProcess

        try:
            all_old_lines = __getFileContents( app, project_info, old_path_info )
            all_new_lines = __getFileContents( app, project_info, new_path_info )

            ok = True

        except IOError, e:
            app.log_error( e )

        yield app.foregroundProcess

        # built-in
        if ok:
            diff_frame = wb_diff_frame.DiffFrame( app, app.frame,
                                all_old_lines, old_path_info.title, all_new_lines, new_path_info.title )
            # only show if the files could be read
            if diff_frame.isOk():
                diff_frame.showAllFolds( False )
                diff_frame.Show( True )

                app.all_diff_frames.append( diff_frame )

def subversionDiffDir(
        app,
        project_info,
        old_path_info,
        new_path_info ):

    # if revision is None cannot ask svn for the contents
    mode = app.prefs.getDiffTool().diff_tool_mode
    app.log.debug( 'subversionDiffDir: mode %r' % mode )

    # svn diff only works on versioned files
    if mode == 'svn-diff' and (old_path_info.revision is None or new_path_info.revision is None):
        mode = 'built-in'

    if mode == 'svn-diff' or True:
        # svn will do all the work
        yield app.backgroundProcess

        if debug_diff:
            old_path_info.printDescription( 'old_path_info' )
            new_path_info.printDescription( 'new_path_info' )

        try:
            if old_path_info.pegIsEqual( new_path_info ):
                if debug_diff:
                    print 'diff_peg:'
                    print '   url_or_path %r' % new_path_info.peg_path
                    print '  peg_revision %r' % new_path_info.peg_revision
                    print 'revision_start %r' % old_path_info.revision
                    print '  revision_end %r' % new_path_info.revision
                    print '       recurse %r' % True

                diff_text = project_info.client_bg.diff_peg(
                        tmp_path=tempfile.gettempdir(),
                        url_or_path=new_path_info.peg_path,
                        peg_revision=new_path_info.peg_revision,
                        revision_start=old_path_info.revision,
                        revision_end=new_path_info.revision,
                        recurse=True )
            else:
                if debug_diff:
                    print 'diff:'
                    print ' url_or_path %r' % old_path_info.path
                    print '   revision1 %r' % old_path_info.revision
                    print 'url_or_path2 %r' % new_path_info.path
                    print '   revision2 %r' % new_path_info.revision
                    print '     recurse %r' % True
                diff_text = project_info.client_bg.diff(
                        tmp_path=tempfile.gettempdir(),
                        url_or_path =old_path_info.path,
                        revision1=old_path_info.revision,
                        url_or_path2=new_path_info.path,
                        revision2=new_path_info.revision,
                        recurse=True )

        except pysvn.ClientError, e:
            # can get here when there are missing files in the WC
            print 'Error: %s' % e.args[0]
            return

        yield app.foregroundProcess

        showDiffText( app, diff_text, old_path_info.title, new_path_info.title )

def __processExternalCommandOptions( app, options, old_filename, old_title, new_filename, new_title ):
    # must have the left and right files
    if '%nl' not in options:
        options = options + ' %nl'
    if '%nr' not in options:
        options = options + ' %nr'

    quote = "'"
    if sys.platform == 'win32':
        quote = '"'

    # quote all replacements
    for ui_format, replacement in   (('%tl', quote + old_title + quote)
                                    ,('%tr', quote + new_title + quote)
                                    ,('%nl', quote + old_filename + quote)
                                    ,('%nr', quote + new_filename + quote)):
        options = options.replace( ui_format, replacement )

    return options

#
#   throws IOError.
#
def __getFileContents( app, project_info, path_info ):    
    all_content_lines = ''
    try:
       if path_info.revision is None or path_info.revision.kind == pysvn.opt_revision_kind.working:
           all_content_lines = wb_read_file.readFileContentsAsUnicode( path_info.path ).split('\n')
    
       else:
           if path_info.revision.kind == pysvn.opt_revision_kind.base:
               all_content_lines = project_info.client_bg.cat(
                   url_or_path=path_info.path,
                   revision=path_info.revision )
    
           else:
               if path_info.peg_revision is not None:
                   all_content_lines = project_info.client_bg.cat(
                       url_or_path=path_info.peg_path,
                       revision=path_info.revision,
                       peg_revision=path_info.peg_revision )
    
               else:
                   all_content_lines = project_info.client_bg.cat(
                       url_or_path=path_info.path,
                       revision=path_info.revision )
    
           all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' ) 

    except pysvn.ClientError, e:
        app.log_client_error( e )
   

    return all_content_lines

#
#   throws IOError.
#
def __getLocalFilename( app, project_info, path_info ):
    rev_description = ''
    all_content = ''
    try:
        if path_info.revision is None or path_info.revision.kind == pysvn.opt_revision_kind.working:
            return path_info.path

        elif path_info.revision.kind == pysvn.opt_revision_kind.base:
            rev_description = 'BASE'
            all_content = project_info.client_bg.cat(
                    url_or_path=path_info.path,
                    revision=path_info.revision )

        else:
            if path_info.revision.kind == pysvn.opt_revision_kind.head:
                rev_description = 'HEAD'
            else:
                rev_description = 'R%d' % path_info.revision.number

            if path_info.peg_revision is not None:
                all_content = project_info.client_bg.cat(
                        url_or_path=path_info.peg_path,
                        peg_revision=path_info.peg_revision,
                        revision=path_info.revision )
            else:
                all_content = project_info.client_bg.cat(
                        url_or_path=path_info.path,
                        revision=path_info.revision )
    except pysvn.ClientError, e:
        app.log_client_error( e )

    # create a temp file with a name that is based on the original filename
    prefix = 'tmp-%s-%s-' % (os.path.basename( path_info.path ), rev_description)
    suffix = os.path.splitext( path_info.path )[1]
    fd, filename = tempfile.mkstemp( prefix=prefix, suffix=suffix )
    os.write( fd, all_content )
    os.close( fd )

    # keep track of the temp file
    app.all_temp_files.append( filename )

    # return name to caller
    return filename

def showDiffText( app, text, old_title, new_title ):
    show_diff_frame = wb_show_diff_frame.ShowDiffFrame( app, text, old_title, new_title )

    app.all_diff_frames.append( show_diff_frame )
