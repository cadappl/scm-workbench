'''
 ====================================================================
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_configspec.py

'''

import os

__version__ = '1.2'

# return the separated words and set the offset in the dictorary 'env'
def getWordFromLine( context, env=dict(), delimiter=None ):
    if context is None:
        return None, None

    if delimiter:
        words = list()
        de_str = context.strip()
        if len( de_str ) > 0 and delimiter.find( de_str[0] ) > -1:
            # "' fooo ' bar " -> [ "", " fooo ", " bar " ]
            de_words = de_str.split( de_str[0] )
            if len( de_words ) > 2:
                second = de_words[2].lstrip() + delimiter.join( de_words[3:] )
                words.append( de_words[1] )
                words.append( second )
            else:
                delimiter = None
        else:
            delimiter = None

    if delimiter is None:
        words = context.split( delimiter, 1 )

    if len( words ) > 1:
        env['offset'] = env.get('offset', 0) + context.find( words[1] )

        return words[0], words[1]
    else:
        return words[0], None

class ConfigspecRule:
    def __init__ ( self, scope, lineno, context, env=dict(), opts=dict() ):
        self.scope = scope
        self.lineno = lineno
        self.context = context
        self.env = env
        self.opts = opts

    def dump( self ):
        return self.context

    def filter( self, args ):
        for k in args.keys():
            v = k
            ret = True
            reversed = True
            if k.startswith( 'not-' ):
                v = k[4:]
                reversed = False

            if self.opts.has_key( v ):
                if isinstance( self.opts[v], ( list, tuple ) ) \
                and args[k] in self.opts[v]:
                    ret = reversed
                elif self.opts[v].find( args[k] ) > -1:
                    ret = reversed

            # retrun false only
            if ret == False:
                break

        return True

    def match( self, sci_path ):
        return False

    def get( self, opt=None ):
        if isinstance( opt, ( list, tuple ) ):
            ret = list()
            for o in opt:
                ret.append( self.opts.get( o ) )

            return ret
        else:
            return self.opts.get( opt )

    def set( self, opt, value ):
        self.opts[opt] = value

    def getError( self ):
        return self.env['error']

    def getRepository( self ):
        return None

class Error( ConfigspecRule ):
    def __init__ ( self, lineno, context ):
        env = dict( { 'error':'unknown keyword' } )
        ConfigspecRule.__init__( self, '!!ERROR!!', lineno, context, env )

# # comment
class CommentRule( ConfigspecRule ):
    def __init__( self, lineno, context ):
        ConfigspecRule.__init__( self, '#', lineno, context )

#
# scope pattern version-selector [optional-clause]
#  - scope
#    element
#    element -file
#    element -directory
#    element -eltype element-type
# - pattern
# - version-selector
# - optional clause
#    - time date-time

# selector '-config do-pname [-select do-leaf-pattern] [-ci] isn't support
class ElementRule( ConfigspecRule ):
    def __init__( self, lineno, context, branch_name=list(), date_time=list() ):
        env = dict()
        error = None
        opts = dict()

        # scope
        if branch_name and len( branch_name ):
            opts['branch-name'] = branch_name[-1]

        if date_time and len( date_time ):
            opts['date-time'] = date_time[-1]

        word, tails = getWordFromLine( context, env )
        if word != 'element':
            error = 'mismatch rule?'

        if error is None:
            word, tails = getWordFromLine( tails, env )

            opts['-file'] = word == '-file'
            opts['-directory']  = word == '-directory'
            iself = word == '-elftype'
            if iself:
                word, tails = getWordFromLine( tails, env )
                if word:
                    opts['-elftype'] = word
                    word, tails = getWordFromLine( tails, env )
                else:
                    error = "Parameter of -elftype is missed"

        # pattern
        if error is None:
            if word:
                opts['pattern'] = word.replace( '\\', '/' )
            else:
                error = 'Pattern is missed'

        # version-selector
        if error is None:
            word, tails = getWordFromLine( tails, env, "'" )
            if word:
                opts['version-selector'] = word
                if word == '-conifg':
                    word, tails = getWordFromLine( tails, env )
                    if word:
                        opts['-config'] = word
                    else:
                        error = 'Parameter of -config is missed'

                    if error is None:
                        word, tails = getWordFromLine( tails, env )
                        if word == '-select':
                            word, tails = getWordFromLine( tails, env )
                            if word:
                                opts['-select'] = word
                            else:
                                error = 'Parameter of -select is missed'
                        elif word == '-ci':
                            opts['-ci'] = True
                else:
                    word, tails = getWordFromLine( tails, env )
            else:
                error = 'Version-selector is missed'

        # optional clause
        if error is None:
            if word == '-time':
                word, tails = getWordFromLine( tails, env )
                if word:
                    opts['-time'] = word
                else:
                    error = 'Parameter of -time is missed'

        # analyze the pattern and verson selector
        if error is None:
            # pattern
            p = opts['pattern'].split( '/' )
            if p[0] == '...':
                tp = 'l'
            elif p[-1] == '...':
                tp = 'r'
            elif '...' in p:
                tp = 'm'
            elif p[0] == '*' and len( p ) == 1:
                tp = 'a'
            else:
                tp = 'n'

            opts['_pattern'] = list( [tp, p] )

        env['error'] = error
        ConfigspecRule.__init__( self, 'element', lineno, context, env, opts )

    def match( self, sci ):
        r = True
        s = sci.split( '/' )
        tp, p = self.opts['_pattern']

        lx = min( len( s ), len( p ) )
        if tp == 'l':
            for k in range( lx ):
                if p[-k] == '...':
                    pass
                elif p[-k] != s[-k]:
                    r = False
                    break
        elif tp == 'm':
            # find the first three-dot, and start the 2nd loop, in which, the
            # three-dots will be ignored
            k = 0
            for k in range( lx ):
                if p[k] == '...':
                    break
                elif p[k] != s[k]:
                    r = False
                    break

            if r:
                o = x = 0
                while o >= 0 and x < lx -k:
                    if o < 0:
                        r = False
                        break
                    if p[-( x + o )] == '...':
                        o += 1
                    elif p[-( x + o )] != s[-x]:
                        o -= 1
                    else:
                        x += 1
        elif tp == 'r':
          # SCI should be longer than pattern
  #        print 'l_s=%d,l_p=%d' % (len(s),len(p))
          if len( s ) + 1 < len( p ):
            r = False
          else:
            for k in range( lx ):
              if p[k] == '...':
                pass
              elif p[k] != s[k]:
                r = False
                break
        elif tp == 'n':
          if len( s ) == len( p ):
              for k in range( lx ):
                  if p[k] != s[k]:
                      r = False
                      break

        return r

    def set( self, selector=None, optional=None ):
      if selector:
          self.opts['version-selector'] = selector

      if optional:
          self.opts['optional-clause'] = optional

    def dump( self  ):
        listp = list()

        # scope
        listp.append( self.scope )
        if self.opts.get( '-file', False ):
            listp.append( '-file' )
        elif self.opts.get( '-directory', False ):
            listp.append( '-directory' )
        elif self.opts.has_key(' -elftype' ):
            listp.append( '-elftype %s' % self.opts['-elftype'] )

        # pattern
        listp.append( self.opts.get( 'pattern', '' ) )
        # version-selector
        listp.append( self.opts.get( 'version-selector', '' ) )
        # optional clause
        listp.append( self.opts.get( '-time', '' ) )

        return ' '.join( ' '.join( listp ).split() )

    def getRepository(self):
        return self.opts.get( 'pattern', None )

# mkbranch branch-type-name [-override]
class MkBranchRule( ConfigspecRule ):
    def __init__( self, lineno, rule, branch_name ):
        error = None
        env = dict()
        opts = dict( {'-override' : False} )

        word, tails = getWordFromLine( context, env )
        if word != 'mkbranch':
            error = 'mismatch rule?'

        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word:
                opts['branch-type-name'] = word
            else:
                error = 'branch-type-name is missed'

        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word == '-override':
                opts['-override'] = True

        if k < len(s):
            error = 'Unknown parameter in lineno'
        else:
            branch_name.append( s[k], opts['-override'] )

        env['error'] = error
        ConfigspecRule.__init__( self, 'mkbranch', lineno, context, env, opts )

    def dump(self):
        listp = list()

        listp.append( self.scope )
        if len( self.opts.get( 'branch-type-name', '' ).split() ) > 1:
            listp.append( "'%s'" % self.opts['branch-type-name'] )
        else:
            listp.append( self.opts['branch-type-name'] )

        if self.opts.get( '-override', False ):
            listp.append( '-override' )

        return ' '.join( listp )

# end mkbranch mkbranch-type-name
class EndMkbranchRule( ConfigspecRule ):
    def __init__( self, lineno, context, branch_name ):
        env = dict()
        error = None
        opts = dict()

        word, tails = getWordFromLine( context, env )
        if word != 'end':
            error = 'mismatch rule?'
        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word != 'branch':
                error = 'mismatch rule for?'

        if len( branch_name ) == 0:
            error = 'no branch-name defined'

        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word:
                opts['branch-type-name'] = word
                if word != branch_name[-1]:
                    error = 'branch-type-name "%s" mismatch last branch "%s"' % ( word, branch_name[-1] )
                else:
                    branch_name.pop( -1 )
            else:
                error = 'Branch-type-name is missed'

        env['error'] = error
        ConfigspecRule.__init__( self, 'end branch', lineno, context, env, opts )

    def dump(self):
        listp = list()
        listp.append( self.scope )
        listp.append( self.opts.get( 'branch-type-name', '') )

        return ' '.join( listp )

# time date-time
class TimeRule( ConfigspecRule ):
    def __init__( self, lineno, rule, date_time ):
        error = None
        env = dict()
        opts = dict()

        word, tails = getWordFromLine( context, env )
        if word != 'time':
            error = 'mismatch rule?'

        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word:
                opts['date-time'] = word
                date_time.append( word )
            else:
                error = 'date-time is missed'

        env['error'] = error
        ConfigspecRule.__init__( self, 'time', lineno, context, env, opts )

    def dump( self ):
        listp = list()
        listp.append( self.scope )
        listp.append( self.opts.get( 'date-time', '') )

        return ' '.join( listp )

# end time [date-time]
class EndTimeRule( ConfigspecRule ):
    def __init__( self, lineno, rule, date_time ):
        env = dict()
        error = None
        opts = dict()

        word, tails = getWordFromLine( context, env )
        if word != 'end':
            error = 'mismatch rule?'
        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word != 'time':
                error = 'mismatch rule for?'

        if len( date_time ) == 0:
            error = 'no date-time defined'

        if error is None:
            word, tails = getWordFromLine( tails, env )
            if word:
                opts['date-time'] = word
                if word != date_time[-1]:
                    error = 'branch-type-name "%s" mismatch last branch "%s"' % ( word, date_time[-1] )
                else:
                    date_time.pop( -1 )
            else:
                error = 'Branch-type-name is missed'

        env['error'] = error
        ConfigspecRule.__init__( self, 'end', lineno, rule, env, opts )

    def dump( self ):
        listp = list()
        listp.append( self.scope )
        listp.append( self.opts.get( 'date-time', '') )

        return ' '.join( listp )

# include config-spec-pname
class IncludeRule( ConfigspecRule ):
    def __init__( self, lineno, rule, branch_name, date_time ):
        error = None
        env = dict()
        opts = dict()

        word, tails = getWordFromLine( context, env )
        if word != 'include':
            error = 'mismatch rule?'

        if error is None:
            word, tails = getWordFromLine( tails, env, "'" )
            if word:
                opts['config-spec-pname'] = s[k]
            else:
                error = 'Config-spec-pname missed'

        # FIXME: implement the include rule here ...
        env['error'] = error
        ConfigspecRule.__init__( self, 'include', lineno, rule, env, opts )

    def dump( self ):
        listp = list()
        listp.append( self.scope )
        listp.append( self.opts.get( 'config-spec-pname', '') )

        return ' '.join( listp )

# load pname
class LoadRule( ConfigspecRule ):
    def __init__( self, lineno, rule ):
        error = None
        env = dict()
        opts = dict()

        word, tails = getWordFromLine( context, env )
        if word != 'load':
            error = 'mismatch rule?'

        if error is None:
            word, tails = getWordFromLine( tails, env, '\'"' )
            if word:
                opts['pname'] = s[k]
            else:
                error = 'pname missed'

        env['error'] = error
        ConfigspecRule.__init__( self, 'load', lineno, rule, env, opts )

    def dump( self ):
        listp = list()
        listp.append( self.scope )
        listp.append( self.opts.get( 'pname', '') )

        return ' '.join( listp )

    def getRepository( self ):
        return self.opts.get( 'pname', None )

class Configspec:
    def __init__ ( self, configspec='', configspec_file='' ):
        self.configspec = configspec

        lines = configspec.split( '\n' )
        self.perror = self.parse( lines )

    def error ( self ):
        return self.perror

    def parse ( self, lines ):
        date_time = list()
        branch_name = list()

        self.parsed_lines = list()
        for k, lo in enumerate( lines ):
            #print "Line %d: %s" % (k, lo)
            off_hash = lo.find( '#' )
            if off_hash > -1:
                rp = CommentRule( k, lo[off_hash:] )
                self.parsed_lines.append( rp )
                lo = lo[:off_hash]

            for li in lo.split( ';' ):
                li = li.strip()

                if len( li ) == 0 or li.startswith( '#' ):
                    continue

                lz = li.split()
                #print 'lz=', lz, 'li=', li
                #= element
                if lz[0] == 'element':
                    rp = ElementRule( k, lo, branch_name, date_time )
                #= load pname (for snapshot views)
                elif lz[0] == 'load':
                    rp = LoadRule( k, lo )
                #= mkbranch branch-type-name [-override]
                elif lz[0] == 'mkbranch':
                    rp = MkBranchRule( k, lo, branch_name )
                #= time date-time
                elif lz[0] == 'time':
                    rp = TimeRule( k, lo, date_time )
                #= end time [date-time]
                elif len(lz) > 1 and lz[0] == 'end' and lz[1] == 'time':
                    rp = EndTimeRule( k, lo, date_time )
                #= end mkbranch [branch-type-name]
                elif len(lz) > 1 and lz[0] == 'end' and lz[1] == 'branch':
                    rp = MkBranchRule( k, lo, branch_name )
                #= include config-spec-pname
                elif lz[0] == 'include':
                    rp = IncludeRule( k, lo, branch_name, date_time )
                else:
                    rp = Error( k, lo )

                if rp.getError() is not None:
                    return 'Line %d: Error - %s' % ( rp.lineno, rp.getError() )

                self.parsed_lines.append( rp )

        return None

    def match( self, root, sci, prefix ):
        ret = list()

        if root.endswith( '/' ):
            root = root[:-1]
        if prefix.endswith( '/' ):
            prefix = prefix[:-1]

        sci = sci.replace( root, prefix ).replace( '\\', '/' )
        for item in self.parsed_lines:
            if item.match( sci ):
              ret.append( item )

        if len(ret):
            return ret
        else:
            return None

    def get( self, c, opt ):
          return c.get( opt )

    def set( self, c, opt, value ):
          return c.set( opt, value )

    def getRepositories( self ):
        pnames = list()

        for item in self.parsed_lines:
            repo = item.getRepository()
            if repo and ( repo not in pnames ):
                pnames.append(repo)

        return pnames

    def dump( self ):
        lines = list()
        for rule in self.parsed_lines:
            lines.append( rule.dump() )

        return os.linesep.join( lines )

if __name__ == '__main__':
    cs = '''
element * CHECKEDOUT
element /vobs/package214/integration/... INTEGRATION-1.0
element /vobs/project183/vyp633/...      VYP633-1.0
element * /main/LATEST'''

    pcs = Configspec(cs)
    mlist = pcs.match('E:\z_vyp623_dev', 'E:\z_vyp623_dev/project183/vyp633', '/vobs')
    print "OUTPUT (%d) RULES: " % len(mlist)
    print "--------------------------"
    for rule in mlist:
        print rule.dump()
