'''
 ====================================================================
 Copyright (c) ccc.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_torun_configspec.py

'''

import wb_configspec

def _remove_tail_slash( path ):
  path = path.replace( '\\', '/' )
  if path.endswith( '/' ):
    path = path[:-1]

  return path

class wb_subversion_configspec( wb_configspec.Configspec ):
  __version__ = wb_configspec.__version__

  def __init__( self, configspec='', configspec_file='', rootdir='', prefix='/vobs' ):
    # FIXME: use a setting item instead
    wb_configspec.Configspec.__init__( self, configspec, configspec_file )

    self.prefix = _remove_tail_slash(prefix)
    self.rootdir = _remove_tail_slash(rootdir)

  def convert( self, configspec_rule, sci ):
    br = wb_configspec.Configspec.convert( self, configspec_rule, sci )

  def setRootdir( self, rootdir ):
    self.rootdir = rootdir

  def getRepositories( self ):
    repo = list()
    listp = wb_configspec.Configspec.getRepositories( self )

    prefix = self.prefix
    if not prefix.endswith( '/' ): prefix += '/'
    # filter out all repositories with the prefix
    for p in listp:
      if p.startswith( self.prefix ):
        li = p[ len( self.prefix ) + 1: ]
        li = li[:li.find('/')]
        repo.append(li)

    return repo

  def match( self, repo_map_list, sci ):
    ret = list()

    sci = _remove_tail_slash( sci )
    # filter out CHECKEDOUT
    filted = dict({'not-version-selector' : 'CHECKEDOUT'})
    rp_path = sci.replace( self.rootdir, self.prefix )
    repo = rp_path.replace( '\\', '/' ).split( '/' )[2]
#    print 'rp_path=%s, repo=%s' % (rp_path, repo)
    repo_path = repo_map_list.get( repo, '' )
#    print 'sci=%s,rootdir=%s,prefix=%s' % (sci, self.rootdir, self.prefix)
    rules = wb_configspec.Configspec.match( self, self.rootdir, sci, self.prefix )
#    print 'rules=', rules
    filted_rules = [ r for r in rules or list() if r.filter( filted ) ]
    for rule in filted_rules or list():
      pattern, selector = rule.get( ('pattern', 'selector') )

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
#          print 'tri_dots:%d,pattern_=%s' % (tri_dots, pattern[:tri_dots - 1])
#          print 'rp_path=%s, pattern=%s,post_path=%s,last_dir=%s' % (rp_path, pattern, post_path, last_dir)
          # two solutions referring to VYCdoc30091
          ra = '%s/%s/%s' % ( selector, last_dir, post_path )
          rb = '%s/%s/%s/%s' % ( label, version, last_dir, post_path )
          ret.append( '%s/tags/%s' % ( repo_path, ra.replace( '//', '/' ) ) )
          ret.append( '%s/tags/%s' % ( repo_path, rb.replace( '//', '/' ) ) )
      else:
        #FIXME: add the handler for branch
        pass

    return ret
