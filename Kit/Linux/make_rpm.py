#
#	make_rpm.py
#
import os

print 'Info: setup_version_handling.py'
import sys
import glob
import pysvn
import time
sys.path.append( '../../Source' )
import wb_version

wb_version_string = '%d.%d.%d-%d' % (wb_version.major, wb_version.minor, wb_version.patch, wb_version.build)
wb_version_package_release_string = '%d' % wb_version.build
wb_version_package_string = '%d.%d.%d' % (wb_version.major, wb_version.minor, wb_version.patch)
svn_version_string = '%d.%d.%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
svn_compact_version_string = '%d%d%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])

build_time  = time.time()
build_time_str = time.strftime( '%d-%b-%Y %H:%M', time.localtime( build_time ) )

tmpdir = os.path.join( os.getcwd(), 'tmp' )
if os.path.exists( tmpdir ):
	print 'Info: Clean up tmp directory'
	os.system( 'rm -rf tmp' )

print 'Info: Create directories'

for kit_dir in [
	tmpdir,
	os.path.join( tmpdir, 'ROOT' ),
	os.path.join( tmpdir, 'BUILD' ),
	os.path.join( tmpdir, 'SPECS' ),
	os.path.join( tmpdir, 'RPMS' ),
	os.path.join( tmpdir, 'ROOT/usr' ),
	os.path.join( tmpdir, 'ROOT/usr/local' ),
	os.path.join( tmpdir, 'ROOT/usr/local/bin' ),
	os.path.join( tmpdir, 'ROOT/usr/local/workbench' ),
	os.path.join( tmpdir, 'ROOT/usr/local/workbench/support' ),
	os.path.join( tmpdir, 'ROOT/usr/local/workbench/WorkBench_files' ),
	]:
	if not os.path.exists( kit_dir ):
		os.makedirs( kit_dir )


print 'Info: Copy files'
for cp_src, cp_dst_dir_fmt in [
	('../../Source/bin/wb',
		'ROOT/usr/local/workbench'),
	('../../Source/bin/support/*',
		'ROOT/usr/local/workbench/support'),
	('../../Docs/WorkBench.html',
		'ROOT/usr/local/workbench'),
	('../../Docs/WorkBench_files/*.png',
		'ROOT/usr/local/workbench/WorkBench_files'),
	]:
	print 'Info:  cp %s' % cp_src
	os.system( 'cp -f %s tmp/%s' % (cp_src, cp_dst_dir_fmt % locals()) )

has_libdb = os.path.exists( 'tmp/ROOT/usr/local/workbench/support/libdb-4.3.so' )
if has_libdb:
    os.system( 'gzip tmp/ROOT/usr/local/workbench/support/libdb-4.3.so' )

print 'Info: Create tmp/SPECS/workbench.spec'
f = file('tmp/SPECS/workbench.spec','w')
f.write('''BuildRoot:	%(tmpdir)s/ROOT
Name:		pysvn_workbench_svn%(svn_compact_version_string)s
Version:	%(wb_version_package_string)s
Group:		Development/Libraries
Release:	%(wb_version_package_release_string)s
Summary:	pysvn WorkBench %(wb_version_string)s for Subversion %(svn_version_string)s
License:	Apache Software License, Version 1.1 - Copyright Barry A. Scott (c) 2003-2007
Packager:	Barry A. Scott <barry@barrys-emacs.org>
AutoReqProv:	no
Requires:	libsvn_client-1.so.0
%%description
PySVN WorkBench %(wb_version_string)s for Subversion %(svn_version_string)s

Copyright Barry A. Scott (c) 2003-2007

mailto:barry@barrys-emacs.org
http://pysvn.tigris.org

     Barry Scott

%%define __spec_install_post %%{nil}
%%prep
%%build
%%install
%%post
rm -f /usr/local/bin/workbench
ln -f -s /usr/local/workbench/wb /usr/local/bin/workbench
if [ -e /usr/local/workbench/support/libdb-4.3.so.gz ]
then
    gzip -d -c </usr/local/workbench/support/libdb-4.3.so.gz >/usr/local/workbench/support/libdb-4.3.so
fi
mkdir -p /usr/local/share/workbench
ln -f -s /usr/local/workbench/WorkBench.html /usr/local/share/workbench
%%postun
# check the arg to find out if this is an update or a delete
# 0 - delete, 1 - update
if [ $1 = 0 ]
then
    rm -f /usr/local/bin/workbench
    rm -rf /usr/local/share/workbench
    rm -f /usr/local/workbench/support/libdb-4.3.so
fi
%%files
%%defattr (-,root,root)
%%attr(555,root,root) /usr/local/workbench/wb
%%attr(444,root,root) /usr/local/workbench/WorkBench.html
''' % locals() )

for name in glob.glob('tmp/ROOT/usr/local/workbench/support/*'):
	f.write( '%%attr(444,root,root) /usr/local/workbench/support/%s\n' % os.path.basename( name ) )

for name in glob.glob('tmp/ROOT/usr/local/workbench/WorkBench_files/*'):
	f.write( '%%attr(444,root,root) /usr/local/workbench/WorkBench_files/%s\n' % os.path.basename( name ) )
f.close()

print 'Info: Create rpmrc'
os.system('grep ^macrofiles: /usr/lib/rpm/rpmrc |sed -e s!~/.rpmmacros!%(tmpdir)s/rpmmacros! >%(tmpdir)s/rpmrc' % locals() )
print 'Info: Create rpmmacros'
f = file( 'tmp/rpmmacros', 'w' )
f.write( '%%_topdir %(tmpdir)s' % locals() )
f.close()
print 'Info: rpmbuild'
os.system( 'rpmbuild --rcfile=/usr/lib/rpm/rpmrc:%(tmpdir)s/rpmrc -bb %(tmpdir)s/SPECS/workbench.spec' % locals() )
