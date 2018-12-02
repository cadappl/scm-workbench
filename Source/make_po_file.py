#!/bin/sh
import sys
import os

import wb_version
import datetime

args = {'WB_LOCALE': sys.argv[1]}

if os.path.exists( 'I18N/pysvn_workbench_%(WB_LOCALE)s.po' % args ):
    print 'Info: Update %(WB_LOCALE)s from I18N/pysvn_workbench.current.pot' % args
    rc = os.system( 'msginit '
        '--input=I18N/pysvn_workbench.current.pot '
        '--locale=${WB_LOCALE} '
        '--no-wrap '
        '--no-translator '
        '--output-file=I18N/pysvn_workbench_%(WB_LOCALE)s.tmp.po' % args )
    if rc != 0:
        sys.exit( rc )

    rc = os.system( 'msgmerge '
        'I18N/pysvn_workbench_%(WB_LOCALE)s.po '
        'I18N/pysvn_workbench_%(WB_LOCALE)s.tmp.po '
        '--quiet '
        '--no-wrap '
        '--output-file=I18N/pysvn_workbench_%(WB_LOCALE)s.current.po' % args )
    if rc != 0:
        sys.exit( rc )

else:
    print 'Info: Create %(WB_LOCALE)s from I18N/pysvn_workbench.current.pot' % args
    rc = os.system( 'msginit '
        '--input=I18N/pysvn_workbench.current.pot '
        '--locale=%(WB_LOCALE)s.UTF-8 '
        '--no-wrap '
        '--no-translator '
        '--output-file=I18N/pysvn_workbench_%(WB_LOCALE)s.current.po' % args )
    if rc != 0:
        sys.exit( rc )

print 'Info: Version brand %(WB_LOCALE)s from I18N/pysvn_workbench.current.pot' % args
po_filename = 'I18N/pysvn_workbench_%(WB_LOCALE)s.current.po' % args
all_po_lines = open( po_filename, 'r' ).readlines()

for index, line in enumerate( all_po_lines ):
    if line.startswith( '"Project-Id-Version:' ):
        all_po_lines[ index ] = ('"Project-Id-Version: WorkBench %d.%d.%d.%d\\n"\n' % 
            (wb_version.major
            ,wb_version.minor
            ,wb_version.patch
            ,wb_version.build))

    elif line.startswith( '"PO-Revision-Date:' ):
        all_po_lines[ index ] = '"PO-Revision-Date: %s\\n"\n' % (datetime.datetime.now().isoformat(' '),)

    elif line.startswith( '"Content-Type: text/plain; charset=' ):
        all_po_lines[ index ] = '"Content-Type: text/plain; charset=UTF-8\\n"\n'

open( po_filename, 'w' ).write( ''.join( all_po_lines ) )
sys.exit( 0 )
