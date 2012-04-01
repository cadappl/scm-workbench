'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_macosx_commands.py

'''
import os
import signal
import subprocess
import xml.sax.saxutils

import wb_platform_specific

__sigchld_handler_installed = False

def getTerminalProgramList():
    return ['Terminal','iTerm']

def getFileBrowserProgramList():
    return ['Finder']

def GuiDiffFiles( app, options ):
    cmd_line = u"'%s' %s &" % (app.prefs.getDiffTool().gui_diff_tool, options)
    app.log.info( cmd_line )
    __run_command_with_output( cmd_line )

def ShellDiffFiles( app, options ):
    cmd_line = u"'%s' %s" % (app.prefs.getDiffTool().shell_diff_tool, options)
    app.log.info( cmd_line )
    return __run_command_with_output( cmd_line )

def EditFile( app, project_info, filename ):
    p = app.prefs.getEditor()

    if p.editor_image:
        if p.editor_options:
            command_line = (u'"%s" %s "%s" &' %
                (p.editor_image, p.editor_options, filename))
        else:
            command_line = (u'"%s" "%s" &' %
                (p.editor_image, filename))
    else:
        command_line = (u'"open" -e "%s" &' %
                            (filename,))

    app.log.info( command_line )
    cur_dir = os.getcwd()
    try:
        wb_platform_specific.uChdir( project_info.getWorkingDir() )
        os.system( command_line.encode( 'utf-8' ) )
    finally:
        wb_platform_specific.uChdir( cur_dir )

def ShellOpen( app, project_info, filename ):
    app.log.info( T_('Open %s') % filename )
    cur_dir = os.getcwd()
    try:
        wb_platform_specific.uChdir( project_info.getWorkingDir() )
        __run_command_with_output( u'open "%s"' % (filename,) )
    finally:
        wb_platform_specific.uChdir( cur_dir )

def CommandShell( app, project_info ):
    p = app.prefs.getShell()
    if p.shell_terminal == 'iTerm':
        CommandShell_iTerm( app, project_info )
    else:
        CommandShell_Terminal( app, project_info )

def CommandShell_iTerm( app, project_info ):
    shell_script_filename = os.path.join( '/tmp', 'wb.scpt' )

    p = app.prefs.getShell()
    working_dir = project_info.getWorkingDir()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = []
    pi = project_info
    while pi:
        title.append( pi.project_name )
        pi = pi.parent

    commands = u'cd "%s"' % working_dir

    if len( p.shell_init_command ) > 0:
        commands = commands + u';. "%s"\n' % p.shell_init_command

    contents = u'''
tell application "iTerm"
    activate 

    -- make a new terminal
    set work_bench_term to (make new terminal) 

    -- talk to the new terminal
    tell work_bench_term 
        activate current session
        launch session "Default Session"

        -- talk to the session
        tell the last session
            set name to "%s"

            -- execute a command
            exec command "/bin/bash"

            write text "%s"

        end tell

    end tell

end
''' %   (' '.join( title ).replace( '"', '\\"' )
        ,commands.replace( '"', '\\"' ))

    f = wb_platform_specific.uOpen( shell_script_filename, 'w' )
    f.write( contents.encode( 'utf-8' ) )
    f.close()

    command_line = u'"osascript" "%s" &' % shell_script_filename

    app.log.info( command_line )
    __run_command_with_output( command_line )

def CommandShell_Terminal( app, project_info ):
    shell_script_filename = os.path.join( '/tmp', 'wb.term' )

    p = app.prefs.getShell()
    working_dir = project_info.getWorkingDir()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = []
    pi = project_info
    while pi:
        title.append( pi.project_name )
        pi = pi.parent

    commands = u'cd "%s"' % working_dir

    if len( p.shell_init_command ) > 0:
        commands = commands + ';. "%s"\n' % p.shell_init_command

    contents = u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WindowSettings</key>
    <array>
        <dict>
            <key>CustomTitle</key>
            <string>%s</string>
            <key>ExecutionString</key>
            <string>%s</string>
        </dict>
    </array>
</dict>
</plist>
''' %   (xml.sax.saxutils.escape( ' '.join( title ) )
        ,xml.sax.saxutils.escape( commands ))

    f  = wb_platform_specific.uOpen( shell_script_filename, 'w' )
    f.write( contents.encode( 'utf-8' ) )
    f.close()

    command_line = u'"open" "%s" &' % shell_script_filename

    app.log.info( command_line )
    __run_command_with_output( command_line )

def FileBrowser( app, project_info ):
    command_line = u'open -a "Finder" "%s" &' % project_info.getWorkingDir()

    app.log.info( command_line )
    __run_command_with_output( command_line )

def __sigchld_handler( signum, frame ):
    try:
        while True:
            pid, status = os.waitpid( -1, os.WNOHANG )
            if pid == 0:
                break

    except OSError, e:
        pass

def _run_command( command_line ):
    err_prefix = 'Error running %s' % command_line

    # install the sig child handler to get rid of the zomie processes
    global __sigchld_handler_installed
    if not __sigchld_handler_installed:
        signal.signal( signal.SIGCHLD, __sigchld_handler )
        __sigchld_handler_installed = True

    try:
        proc = subprocess.Popen(
                    command_line,
                    shell=True,
                    close_fds=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                    )

        output = proc.stdout.read()
        rc = proc.wait()

    except EnvironmentError, e:
        print '%s - %s' % (err_prefix, str(e))
        return

    # check for OK
    if os.WIFEXITED( rc ):
        print output
        return

    # some error
    print '%s, rc=%d' % (err_prefix, rc)

def __run_command_with_output( command_line ):
    err_prefix = u'error running %s' % command_line

    try:
        proc = subprocess.Popen(
                    command_line.encode( 'utf-8' ),
                    shell=True,
                    close_fds=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                    )

        output = proc.stdout.read()
        rc = proc.wait()

    except EnvironmentError, e:
        return '%s - %s' % (err_prefix, str(e))

    # check for OK
    if os.WIFEXITED( rc ):
        return output

    # some error
    return '%s, rc=%d' % (err_prefix, rc)
