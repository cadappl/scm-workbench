#
# make_wb_bundle.py
#
import bundlebuilder
import sys
import pysvn
import shutil
import glob

# make sure that we get 2.6 and not an earlier version
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select( ['2.6', '2.8'] )

import wx
import os
import traceback


def findDylibs( image, dylib_list, depth=0 ):
    cmd = 'otool -L "%s" >/tmp/pysvn_otool.tmp' % image
    #print 'Debug: cmd %r' % cmd
    os.system( cmd )
    # always skip the first line that lists the image being dumped
    for line in file( '/tmp/pysvn_otool.tmp' ).readlines()[1:]:
        line = line.strip()
        #print 'Debug: line %r' % line
        if( line.startswith( '/' )
        and not line.startswith( '/usr/lib' )
        and not line.startswith( '/System' ) ):
            libpath = line.split()[0]
            if libpath not in dylib_list:
                print 'Info: ',depth,' Need lib',libpath,'for',image
                dylib_list.append( libpath )
                findDylibs( libpath, dylib_list, depth+1 )
        

try:
    # workbench sources
    sys.path.append( '../../Source' )
    # the pysvn package
    sys.path.append( '../../../Extension/Source' )

    # Create the AppBuilder
    myapp = bundlebuilder.AppBuilder( verbosity=1 )

    # Tell it where to find the main script - the one that loads on startup
    myapp.mainprogram = '../../Source/wb_main.py'
    myapp.standalone = 1
    myapp.name = 'WorkBench.app'
    myapp.iconfile = '../../Source/wb.icns'

    # create the bundle here
    myapp.builddir = sys.argv[1]

    # includePackages forces certain packages to be added to the app bundle
    #myapp.includePackages.append("Menu")

    # Here you add supporting files and/or folders to your bundle
    myapp.files.append( ('../../Source/locale', 'Contents/Resources/locale') )
    for locale_lang_root in glob.glob( '../../Source/locale/??' ):
        myapp.resources.append( os.path.join( locale_lang_root, 'LC_MESSAGES/pysvn_workbench.mo' ) )

    # bundlebuilder does not yet have the capability to detect what shared libraries
    # are needed by your app - so in this case I am adding the wxPython libs manually

    py_ver = '%d.%d' % (sys.version_info[0], sys.version_info[1])

    wx_ver = '%d.%d.%d.%d%s' % wx.VERSION
    wx_3ver = '%d.%d.%d' % wx.VERSION[0:3]
    wx_2ver = '%d.%d.0' % wx.VERSION[0:2]

    for libname_fmt in [
            "/usr/local/lib/wxPython-unicode-%s/lib/libwx_macud-%s.dylib",
            "/usr/local/lib/wxPython-unicode-%s/lib/libwx_macud_gl-%s.dylib",
            "/usr/local/lib/wxPython-unicode-%s/lib/libwx_macud_gizmos-%s.dylib",
            "/usr/local/lib/wxPython-unicode-%s/lib/libwx_macud_stc-%s.dylib",
            ]:
        for args in [(wx_ver, wx_3ver),(wx_ver, wx_2ver)]:
            lib_found = False
            libname = libname_fmt % args
            if os.path.exists( libname ):
                print 'Info: Manually adding lib %s' % libname
                myapp.libs.append( libname )
                lib_found = True
        if not lib_found:
            raise ValueError( 'Cannot find lib %s' % libname )

    print 'Info: Finding dylibs used by pysvn'
    findDylibs( pysvn._pysvn.__file__, myapp.libs )

    # Here we build the app!
    myapp.setup()
    myapp.build()

    # remove unnecessary files
    os.system( 'pwd' )
    doc_path = os.path.join( sys.argv[1],
        'WorkBench.app/Contents/Frameworks/Python.framework/Versions/%s/Resources/English.lproj/Documentation' % py_ver )
    print doc_path
    shutil.rmtree( doc_path )
except:
    traceback.print_exc( file=sys.stderr )
    sys.exit( 1 )

sys.exit( 0 )
