'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.
 Copyright (c) 2010-2011 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_main.py

'''
import warnings
import sys
import os
import locale

# need to import so that it
import _strptime


# help debug when stdout goes nowhere useful
# Mac OS X and Windows are the main problems
stdout_filename = None

if( os.environ.get( 'PYSVN_WORKBENCH_STDOUT_LOG', None ) is not None
or (sys.platform == 'darwin' and '--noredirect' not in sys.argv) ):
    stdout_filename = os.environ.get( 'PYSVN_WORKBENCH_STDOUT_LOG', '/tmp/workbench.tmp' )

elif sys.platform.startswith( 'win' ):
    stdout_filename = os.path.join( os.environ[ 'TEMP' ], 'workbench.tmp' )

if stdout_filename is not None:
    try:
#        sys.stdout = open( stdout_filename, 'w' )
#        sys.stderr = sys.stdout
        print 'PySVN WorkBench starting'
        sys.stdout.flush()

    except EnvironmentError:
        pass

# make sure that we get 2.8 and not an earlier version
try:
    import wxversion
    wxversion.select( ['2.8'] )
except:
    pass

startup_dir = os.getcwd()
sys.path += ( os.path.join( startup_dir, 'platform' ),
              os.path.join( startup_dir, 'manifest' ) )

import wb_app
import wb_utils

def prerequesitChecks():
    return 1

def main( args ):

    if True:
        if sys.platform == 'win32':
            os.chdir( os.environ['USERPROFILE'] )
            # Fix for wxPython bug on multi-processor machines - limit us to 1 processor
            #win32process.SetProcessAffinityMask(win32api.GetCurrentProcess(), 1)
        else:
            os.chdir( os.environ['HOME'] )

    # don't pollute any subprocesses with env vars
    # from packaging processing
    for envvar in ['PYTHONPATH', 'PYTHONHOME', 'PYTHONEXECUTABLE']:
        if os.environ.has_key( envvar ):
            del os.environ[ envvar ]

    # init the locale
    initLocale()

    # Register all supported source control providers
    wb_utils.loadExts( startup_dir )

    # Create the win application and start its message loop
    app = wb_app.WbApp( startup_dir, args )

    if not prerequesitChecks():
        return 1

    app.frame.Show( 1 )

    app.MainLoop()

    return 0

def initLocale():
    # init the locale
    if sys.platform == 'win32':
        locale.setlocale( locale.LC_ALL, '' )

    else:
        if 'LC_ALL' in os.environ:
            try:
                locale.setlocale( locale.LC_ALL, os.environ['LC_ALL'] )
                return
            except locale.Error:
                pass

        language_code, encoding = locale.getdefaultlocale()
        if language_code is None:
            language_code = 'en_US'

        if encoding is None:
            encoding = 'UTF-8'
        if encoding.lower() == 'utf':
            encoding = 'UTF-8'

        try:
            # setlocale fails when params it does not understand are passed
            locale.setlocale( locale.LC_ALL, '%s.%s' % (language_code, encoding) )
        except locale.Error:
            try:
                # force a locale that will work
                locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )
            except locale.Error:
                locale.setlocale( locale.LC_ALL, 'C' )

#
# needed to make MEINC Installer notice these packages
# Include all the codecs
#
import encodings
import encodings.aliases
import encodings.ascii
import encodings.base64_codec
import encodings.big5
import encodings.big5hkscs
import encodings.bz2_codec
import encodings.charmap
import encodings.cp037
import encodings.cp1006
import encodings.cp1026
import encodings.cp1140
import encodings.cp1250
import encodings.cp1251
import encodings.cp1252
import encodings.cp1253
import encodings.cp1254
import encodings.cp1255
import encodings.cp1256
import encodings.cp1257
import encodings.cp1258
import encodings.cp424
import encodings.cp437
import encodings.cp500
import encodings.cp737
import encodings.cp775
import encodings.cp850
import encodings.cp852
import encodings.cp855
import encodings.cp856
import encodings.cp857
import encodings.cp860
import encodings.cp861
import encodings.cp862
import encodings.cp863
import encodings.cp864
import encodings.cp865
import encodings.cp866
import encodings.cp869
import encodings.cp874
import encodings.cp875
import encodings.cp932
import encodings.cp949
import encodings.cp950
import encodings.euc_jis_2004
import encodings.euc_jisx0213
import encodings.euc_jp
import encodings.euc_kr
import encodings.gb18030
import encodings.gb2312
import encodings.gbk
import encodings.hp_roman8
import encodings.hz
import encodings.iso2022_jp
import encodings.iso2022_jp_1
import encodings.iso2022_jp_2
import encodings.iso2022_jp_2004
import encodings.iso2022_jp_3
import encodings.iso2022_jp_ext
import encodings.iso2022_kr
import encodings.iso8859_1
import encodings.iso8859_10
import encodings.iso8859_11
import encodings.iso8859_13
import encodings.iso8859_14
import encodings.iso8859_15
import encodings.iso8859_16
import encodings.iso8859_2
import encodings.iso8859_3
import encodings.iso8859_4
import encodings.iso8859_5
import encodings.iso8859_6
import encodings.iso8859_7
import encodings.iso8859_8
import encodings.iso8859_9
import encodings.johab
import encodings.koi8_r
import encodings.koi8_u
import encodings.latin_1
import encodings.mac_cyrillic
import encodings.mac_greek
import encodings.mac_iceland
import encodings.mac_latin2
import encodings.mac_roman
import encodings.mac_turkish
import encodings.palmos
import encodings.ptcp154
import encodings.punycode
import encodings.quopri_codec
import encodings.raw_unicode_escape
import encodings.rot_13
import encodings.shift_jis
import encodings.shift_jis_2004
import encodings.shift_jisx0213
import encodings.string_escape
import encodings.tis_620
import encodings.undefined
import encodings.unicode_escape
import encodings.unicode_internal
import encodings.utf_16
import encodings.utf_16_be
import encodings.utf_16_le
import encodings.utf_7
import encodings.utf_8
import encodings.uu_codec
import encodings.zlib_codec

if sys.version_info >= (2,5,0,'',0):
    import encodings.mac_arabic
    import encodings.mac_centeuro
    import encodings.mac_croatian
    import encodings.mac_farsi
    import encodings.mac_romanian
    import encodings.utf_8_sig

# keep pychecker quite
def __pychecker():
    return encodings.utf_8 and warnings

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )