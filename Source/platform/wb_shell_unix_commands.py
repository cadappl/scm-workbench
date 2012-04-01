'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_unix_commands.py

'''
import os
import signal
import subprocess
import types

import wb_platform_specific

__sigchld_handler_installed = False

gui_terminals = ['gnome-terminal', 'konsole', 'xterm', 'xfce4-terminal']
gui_file_browsers = ['nautilus', 'konqueror', 'thunar', 'dolphin']

def getTerminalProgramList():
    return gui_terminals[:]

def getFileBrowserProgramList():
    return gui_file_browsers[:]

def EditFile( app, project_info, filename ):
    p = app.prefs.getEditor()

    if p.editor_image:
        if p.editor_options:
            editor_image = p.editor_image
            editor_args = [p.editor_options, filename]
        else:
            editor_image = p.editor_image
            editor_args = [filename]
    else:
        editor_image = 'kedit'
        editor_args = [filename]

    cur_dir = os.getcwd()
    try:
        wb_platform_specific.uChdir( project_info.getWorkingDir() )
        __run_command( app, editor_image, editor_args )

    finally:
        wb_platform_specific.uChdir( cur_dir )

def ShellOpen( app, project_info, filename ):
    app.log.info( T_('Open %s') % filename )
    cur_dir = os.getcwd()
    try:
        wb_platform_specific.uChdir( project_info.getWorkingDir() )
        os.system( "xdg-open '%s'" % filename )
    finally:
        wb_platform_specific.uChdir( cur_dir )

def GuiDiffFiles( app, options ):
    cmd_line = "'%s' %s &" % (app.prefs.getDiffTool().gui_diff_tool, options)
    app.log.info( cmd_line )
    os.system( cmd_line )

def ShellDiffFiles( app, options ):
    cmd_line = "'%s' %s" % (app.prefs.getDiffTool().shell_diff_tool, options)
    app.log.info( cmd_line )
    return __run_command_with_output( cmd_line )

def CommandShell( app, project_info ):
    shell_script_filename = os.path.join( os.environ.get('TMP','/tmp'), 'wb_shell_tmp.sh' )

    p = app.prefs.getShell()
    working_dir = project_info.getWorkingDir()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = []
    pi = project_info
    while pi:
        title.append( pi.project_name )
        pi = pi.parent

    f  = wb_platform_specific.uOpen( shell_script_filename, 'w' )
    f.write( 'export WB_WD="%s"\n' % working_dir )
    f.write( 'cd "%s"\n' % working_dir )

    if len( p.shell_init_command ) > 0:
        f.write( '. "%s"\n' % p.shell_init_command )
    f.write( 'exec $SHELL -i\n' )
    f.close()
    os.chmod( shell_script_filename, 0700 )

    path = os.environ.get("PATH")
    found = False
    for terminal_program in gui_terminals:
        if p.shell_terminal in ['',terminal_program]:
            for folder in path.split( os.pathsep ):
                exe = os.path.join( folder, terminal_program )
                if os.path.isfile(exe):
                    found = True
                    break
        if found:
            break
    if not found:
        return

    if terminal_program == 'konsole':
        __run_command( app, terminal_program,
            ['--title',  ' '.join( title ), '--workdir', working_dir, '-e', '/bin/sh', shell_script_filename] )

    elif terminal_program in ('gnome-terminal', 'xfce4-terminal'):
        __run_command( app, terminal_program,
            ['--title',  ' '.join( title ), '--working-directory', working_dir, '-x', shell_script_filename] )

    elif terminal_program == 'xterm':
        __run_command( app, terminal_program,
            ['-T',  ' '.join( title ), '-e', shell_script_filename] )

def FileBrowser( app, project_info ):
    p = app.prefs.getShell()

    path = os.environ.get("PATH")
    found = False
    for browser_program in gui_file_browsers:
        if p.shell_file_browser in ['',browser_program]:
            for folder in path.split( os.pathsep ):
                exe = os.path.join( folder, browser_program )
                if os.path.isfile(exe):
                    found = True
                    break
        if found:
            break
    if not found:
        return

    if browser_program == 'konqueror':
        __run_command( app, browser_program, ['--mimetype', 'inode/directory', project_info.getWorkingDir()] )

    elif browser_program in ('nautilus', 'thunar', 'dolphin'):
        __run_command( app, browser_program, [project_info.getWorkingDir()] )

def __run_command( app, cmd, args ):
    app.log.info( '%s %s' % (cmd, ' '.join( args ) ) )

    env = os.environ.copy()

    # if this is a frozen with the McMillian Installer fix up the environment
    if '_MEIPASS2' in os.environ:
        for bad_env in ['_MEIPASS2', 'PYTHONPATH']:
            if bad_env in env:
                del env[ bad_env ]
        old_lib_path_parts = env.get('LD_LIBRARY_PATH','del_me').split(':')
        del old_lib_path_parts[0]
        if len(old_lib_path_parts) > 0:
            env[ 'LD_LIBRARY_PATH' ] = ':'.join( old_lib_path_parts )
        else:
            del env[ 'LD_LIBRARY_PATH' ]

    # install the sig child handler to get rid of the zomie processes
    global __sigchld_handler_installed
    if not __sigchld_handler_installed:
        signal.signal( signal.SIGCHLD, __sigchld_handler )
        __sigchld_handler_installed = True

    cmd = asUtf8( cmd )
    args = [asUtf8( arg ) for arg in args]

    os.spawnvpe( os.P_NOWAIT, cmd, [cmd]+args, env )

def asUtf8( s ):
    if type( s ) == types.UnicodeType:
        return s.encode( 'utf-8' )
    else:
        return s

def __sigchld_handler( signum, frame ):
    try:
        while True:
            pid, status = os.waitpid( -1, os.WNOHANG )
            if pid == 0:
                break

    except OSError, e:
        pass

def __run_command_with_output( command_line ):
    err_prefix = 'error running %s' % command_line

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
        return '%s - %s' % (err_prefix, str(e))

    # check for OK
    if os.WIFEXITED( rc ):
        return output

    # some error
    return '%s, rc=%d' % (err_prefix, rc)
