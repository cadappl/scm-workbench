#
#    make_pkg.py
#
import os

print 'Info: setup version info'
import sys
sys.path.insert( 0, '../../Source')
import wb_version
import pysvn
import time
import subprocess


proc = subprocess.Popen(
            'uname -p',
            shell=True,
            close_fds=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
            )
processor = proc.stdout.read().strip()
rc = proc.wait()

def os_system( cmd ):
    print 'Info: %s' % cmd
    sys.stdout.flush()
    if os.system( '%s 2>&1' % cmd ) == 0:
        return
    print 'Error: command failed'
    sys.exit( 1 )

pymaj, pymin, pypat, _, _ = sys.version_info
wb_version_string = '%d.%d.%d-%d' % (wb_version.major, wb_version.minor, wb_version.patch, wb_version.build)
python_version_string = '%d.%d.%d' % (pymaj, pymin, pypat)
pysvnmaj, pysvnmin, pysvnpat, _ = pysvn.version
pysvn_version_string = '%d.%d.%d' % (pysvn.version[0], pysvn.version[1], pysvn.version[2])
svn_version_package_string = '%d%d%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
svn_version_string = '%d.%d.%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])

pkg_filename = 'pysvn_workbench_svn%s-%s-%s' % (svn_version_package_string, wb_version_string, processor)
print 'Info: Packageing %s' % pkg_filename
build_time  = time.time()
build_time_str = time.strftime( '%d-%b-%Y %H:%M', time.localtime( build_time ) )
year = time.strftime( '%Y', time.localtime( build_time ) )
tmpdir = os.path.join( os.getcwd(), 'tmp' )

if os.path.exists( tmpdir ):
    print 'Info: Clean up tmp directory'
    os_system( 'rm -rf tmp' )

print 'Info: Create directories'

for kit_dir in [
    tmpdir,
    os.path.join( tmpdir, '%s' % pkg_filename),
    ]:
    if not os.path.exists( kit_dir ):
        os.makedirs( kit_dir )

print 'Info: Copy files'
for cp_src, cp_dst_dir_fmt in [
    ('../../LICENSE.txt',
        '%s/License.txt' % pkg_filename),
    ('../../Docs/WorkBench.html',
        '%s/WorkBench.html' % pkg_filename),
    ]:
    if os.path.exists( cp_src ):
        cmd = 'cp -f %s tmp/%s' % (cp_src, cp_dst_dir_fmt % locals())
        print 'Info: %s' % cmd
        os_system( cmd )
    else:
        print 'Error: cannot find %s' % cp_src
        sys.exit( 1 )

print 'Info: Export WorkBench_files'
if os.path.exists( '../../Docs/WorkBench_files/.svn' ):
    os_system( 'svn export ../../Docs/WorkBench_files tmp/%s/WorkBench_files' % pkg_filename )
else:
    os_system( 'mkdir tmp/%s/WorkBench_files' % pkg_filename )
    os_system( 'cp ../../Docs/WorkBench_files/* tmp/%s/WorkBench_files' % pkg_filename )

print 'Info: Create tmp/ReadMe.html'
f = file('tmp/ReadMe.html','w')
f.write('''<html>
<body>
<h1>pysvn WorkBench %(wb_version_string)s for Mac OS X and Subversion %(svn_version_string)s</h1>

<h2>Copyright Barry A. Scott (c) 2003-%(year)s</h2>

<h2>Mail <a href="mailto:barry@barrys-emacs.org">barry@barrys-emacs.org</a></h2>

<h2>Pysvn home <a href="http://pysvn.tigris.org">http://pysvn.tigris.org</a></h2>

<h2>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Barry Scott</h2>
</body>
</html>
''' % locals() )
f.close()

print 'Info: python bundle'
os_system( '${PYTHON} -u make_wb_bundle.py tmp/%s' % pkg_filename)

print 'Info: Make Disk Image'
os_system( 'hdiutil create -srcfolder tmp/%s tmp/tmp.dmg' % pkg_filename )
os_system( 'hdiutil convert tmp/tmp.dmg -format UDZO -imagekey zlib-level=9 ' 
        '-o tmp/%s.dmg' % pkg_filename )
