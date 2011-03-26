'''
 ====================================================================
 Copyright (c) ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_configspec.py

'''

import re
import wb_configspec

def compare( x, y ):
    (ax, bx, ay, by) = (x, y, '0', '0')
    mx = re.match( '([^0-9]+)([0-9]+)', x)
    if mx: ax, ay = mx.group(1), mx.group(2)
    my = re.match( '([^0-9]+)([0-9]+)', y)
    if my: bx, by = my.group(1), my.group(2)

    if cmp(ax, bx) == 0:
        try:
            return int(ay, 10) - int(by, 10)
        except:
            return 0
    else:
        return cmp( ax, bx )

def remove_tail_slash( path ):
    path = path.replace( '\\', '/' )
    if path.endswith( '/' ):
        path = path[:-1]

    return path

class wb_subversion_configspec( wb_configspec.Configspec ):
  __version__ = wb_configspec.__version__

  def __init__( self, configspec='', configspec_file='', rootdir='', prefix='/vobs' ):
    # FIXME: use a setting item instead
    wb_configspec.Configspec.__init__( self, configspec, configspec_file )

    self.prefix = remove_tail_slash( prefix )
    self.rootdir = remove_tail_slash( rootdir )

  def __buildupPath( self, fmt, listp ):
      ret = fmt % listp
      if len( ret ) and ret[-1] == '/':
          ret = ret[:-1]

      return ret

  def replacePrefix( self, file_path ):
      new_path = file_path.replace( root, prefix ).replace( '\\', '/' )

      return new_path

  def getRepositories( self ):
      repo = list()
      listp = wb_configspec.Configspec.getRepositories( self )

      prefix = self.prefix + '/'
      prefix_len = len( prefix )
      # filter out all repositories with the prefix
      for p in listp:
          if p.startswith( prefix ):
              li = p[prefix_len:]
              li = li[:li.find( '/' )]
              if li not in repo: repo.append( li )

      repo.sort( compare )
      return repo

  def match( self, repo_map_list, sci ):
      ret = list()

      sci = remove_tail_slash( sci )
      # filter out CHECKEDOUT
      filted = dict({'not-version-selector' : 'CHECKEDOUT'})
      rp_path = sci.replace( self.rootdir, self.prefix )
      repo = rp_path.replace( '\\', '/' ).split( '/' )[2]

      repo_path = repo_map_list.get( repo, '' )
      rules = wb_configspec.Configspec.match( self, self.rootdir, sci, self.prefix )
      filted_rules = [ r for r in rules or list() if r.filter( filted ) ]

      for rule in filted_rules or list():
          pattern, selector = rule.get( ( 'pattern', 'version-selector' ) )

          selectors = selector.split( '/' )
          if len( selectors ) == 1: # label
              tri_dots = pattern.find( '...' )
              sp = selector.split( '-', 1 )
              label, version = sp[0], '1.0'
              if len(sp) > 1: version = sp[1]
              #FIXME: handle the case "element .../foo FOO-1.0
              if tri_dots > 0:
                  pre_pattern = pattern[:tri_dots - 1]
                  post_path = rp_path.replace( pre_pattern, '')
                  last_dir = pre_pattern.split('/')[-1]
#                 print 'tri_dots:%d,pattern_=%s' % (tri_dots, pattern[:tri_dots - 1])
#                 print 'rp_path=%s, pattern=%s,post_path=%s,last_dir=%s' % (rp_path, pattern, post_path, last_dir)
                  # two solutions referring to VYCdoc30091
                  ra = self.__buildupPath( '%s/%s/%s', ( selector, last_dir, post_path ) )
                  rb = self.__buildupPath( '%s/%s/%s/%s', ( label, version, last_dir, post_path ) )
                  ret.append( '%s/tags/%s' % ( repo_path, ra.replace( '//', '/' ) ) )
                  ret.append( '%s/tags/%s' % ( repo_path, rb.replace( '//', '/' ) ) )
          else:
              #FIXME: add the handler for branch
              pass

      return ret

class wb_subversion_configspec_editor(wb_subversion_configspec):
    def __init__( self, configspec='', configspec_file='', rootdir='', prefix='/vobs' ):
        wb_subversion_configspec.__init__( self, configspec, configspec_file, rootdir, prefix )

    def replace( self, file_path, selector=None ):
        if selector is None:
            slef.delete( file_path )
            return

        # create the corresponding rule to locate the line
        file_rule = self.replacePrefix( remove_tail_slash (file_path ) )
        file_rule += '/...'

        for item in self.parsed_lines:
            if item.match( file_rule ):
                item.set( selector )

    def add( self, file_path, ident, selector, optional=None):
        slots = self.__findTorunSlots()

        new_path = self.replacePrefix( remove_tail_slash (file_path ) )
        pattern = 'element %s/... %s' % ( new_path, selector )

        if slots[ident][1] != -1:
            slotno = slots[ident][1]
        else:
            slots_name = slots.keys()
            slots_name.sort()

            off_name = slots_name.index( ident )
            if off_name < len(slots) - 1:
                slotno = slots[off_name][0] - 1
            else:
                slotno = len( self.parsed_lines )

        lineno = self.parsed_lines[slotno].lineno + 1
        e_rule = wb_configspec.ElementRule( lineno, pattern )
        # adjust the lines after the inserting point
        self.parsed_lines.insert( slotno, e_rule )
        for k, item in enumerate( self.parsed_lines ):
            if k > slotno + 1:
                item.lineno += 1

    def delete( self, file_path ):
        lineno = list()
        new_path = self.replacePrefix( remove_tail_slash (file_path ) )

        # it removes all lines including modules in packages
        for k, item in enumerate( self.parsed_lines ):
            if item.find( new_path ) > -1:
                lineno.append( k )

        lineno.sort()
        lineno.reverse()

        for no in lineno:
            del self.parsed_lines[no]

    def getConfigspec( self ):
        return self.dump()

    def __findTorunSlots( self ):
        # note: the identifier could use sort
        slots = {
          'MODULE': (-1, -1),
          'PACKAGE': (-1, -1),
          'PROJECT': (-1, -1)
        }

        for k, item in enumerate( self.parsed_lines ):
            if isinstance( item, wb_configspec.CommentRule ):
                m = re.match('#(.)={3,5}(.+)$', item.context)
                if m:
                    print '>>', m
                if m and slots.has_key(m[1]):
                    if m[0] == '+':
                        slots[m[1]][0] = k
                    else:
                        slots[m[1]][1] = k

        return slots
