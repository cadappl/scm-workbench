print 'Info: setup_version_handling.py'
import sys
sys.path.insert( 0, '..\\..\\Source')
import wb_version
import pysvn
import time
import os

workbench_version_string = '%d.%d.%d-%d' % (wb_version.major, wb_version.minor, wb_version.patch, wb_version.build)
python_version_string = '%d.%d.%d' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
pysvn_version_string = '%d.%d.%d' % (pysvn.version[0], pysvn.version[1], pysvn.version[2])
svn_version_package_string = '%d%d%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
svn_version_string = '%d.%d.%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])

build_time  = time.time()
build_time_str = time.strftime( '%d-%b-%Y %H:%M', time.localtime( build_time ) )

print 'Info: Create info_before.txt'

f = file('tmp\\info_before.txt','w')
f.write(
'''WorkBench %s for Subversion %s

    Barry Scott

    %s

''' % (workbench_version_string, svn_version_string, build_time_str) )
f.close()

print 'Info: Creating workbench-branded.iss from workbench.iss'
f = file( 'workbench.iss', 'r' )
all_lines = f.readlines()
f.close()
f = file( 'tmp\\workbench-branded.iss', 'w' )
for line in all_lines:
    if line.find( 'AppVerName=' ) == 0:
        f.write( 'AppVerName=WorkBench %s\n' % workbench_version_string )
    else:
        f.write( line )

for filename in os.listdir('..\\..\\source\\bin\\support'):
    if filename.lower() not in ['msvcp60.dll','support']:
        f.write( 'Source: "..\\..\\..\\source\\bin\\support\\%s"; DestDir: "{app}\\Support";\n'
                    % filename )

f.write( 'Source: "..\\..\\..\\docs\\WorkBench.html"; DestDir: "{app}";\n' )

docs_files_dir = '..\\..\\docs\\WorkBench_files'

for filename in os.listdir( docs_files_dir ):
    if os.path.isfile( os.path.join( docs_files_dir, filename ) ):
        f.write( 'Source: "..\\..\\..\\docs\\WorkBench_files\\%s"; DestDir: "{app}\\WorkBench_files";\n'
                    % filename )

locale_files_dir = '..\\..\\Source\\locale'

for lang in os.listdir( locale_files_dir ):
    f.write( 'Source: "..\\..\\..\\Source\\locale\\%s\LC_MESSAGES\\pysvn_workbench.mo"; '
                'DestDir: "{app}\\locale\\%s\LC_MESSAGES";\n'
                    % (lang, lang) )

f.close()

print 'Info: Create setup_copy.cmd'
f = file( 'tmp\\setup_copy.cmd', 'w' )
f.write( 'copy tmp\\Output\\setup.exe tmp\\Output\\pysvn-workbench-svn%s-%s.exe\n' %
    (svn_version_package_string, workbench_version_string) )
f.close()
