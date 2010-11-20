'''
 ====================================================================
 Copyright (c) 2010 ccc. All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_configspec.py

'''

__version__ = '1.0'

class ConfigspecRule:
  def __init__ (self, scope, line, rule, error, slot, opts):
    self.scope = scope
    self.line = line
    self.rule = rule
    self.error = error
    self.slot = slot
    self.opts = opts

  def dump(self):
    return rule

  def filter(self, args):
    for k in args.keys():
      v = k
      ret = True
      reversed = True
      if k.startswith('not-'):
        v = k[4:]
        reversed = False

      if self.opts.has_key(v):
        if isinstance(self.opts[v], (list, tuple)) \
            and args[k] in self.opts[v]:
          ret = reversed
        elif self.opts[v].find(args[k]) > -1:
          ret = reversed

      # retrun false only
      if ret == False:
        return False

    return True

  def match(self, sci):
    return False

  def get(self, item=None):
    return None

  def getRepository(self):
    return None

class Error (ConfigspecRule):
  def __init__ (self, line, rule):
    ConfigspecRule.__init__(self, 'e', line, rule, 'unknown keyword', 0, dict())

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
class ElementRule(ConfigspecRule):
  def __init__(self, line, rule, branch_name, date_time):
    error = None
    opts = dict({'date-time' : date_time})
    is_file = is_dir = is_elf = False
    s = rule.split()

    k = 1 # element
    if k < len(s):
      opts['-file'] = s[k] == '-file'
      opts['-dir']  = s[k] == '-directory'
      is_elf  = s[k] == '-elftype'
      if opts['-file'] or opts['-dir'] or is_elf: k += 1
      if is_elf:
        if k < len(s):
          opts['-elftype'] = s[k]
          k += 1
        else:
          error = "Parameter of -elftype is missed"

    # pattern
    if k < len(s):
      opts['pattern'] = s[k].replace('\\', '/')
      k += 1
    else:
      error = 'Pattern is missed'

    # version-selector
    if k < len(s):
      opts['version-selector'] = s[k]
      # the syntax of -config is verified but not handled
      if s[k] == '-conifg':
        k += 2
        if k < len(s):
          if s[k] == '-select':
            k += 2
            if k >= len(s):
              error = 'Parameter of -select is missed'
          if k < len(s):
            if s[k] == '-ci':
              k += 1
        else:
          error = 'Parameter of -config is missed'
      else:
        k += 1
    else:
      error = 'Version-selector is missed'

    # optional clause
    if k < len(s):
      if s[k] == '-time':
        k += 1
        if k < len(s):
          opts['-time'] = s[k]
          k += 1

    if k < len(s):
      error = 'Unknown parameter in line'

    # analyze the pattern and verson selector
    if error == None:
      # pattern
      p = opts['pattern'].replace('\\', '/').split('/')
      if p[0] == '...':
        tp = 'l'
      elif p[-1] == '...':
        tp = 'r'
      elif '...' in p:
        tp = 'm'
      elif p[0] == '*' and len(p) == 1:
        tp = 'a'
      else:
        tp = 'n'

      opts['_pattern'] = list([tp, p])

    ConfigspecRule.__init__(self, 'E', line, rule, error, k, opts)

  def match(self, sci):
    r = True
    s = sci.split('/')
    tp, p = self.opts['_pattern']

    lx = min(len(s), len(p))
    if tp == 'l':
      for k in range(lx):
        if p[-k] == '...':
          pass
        elif p[-k] != s[-k]:
          r = False
          break
    elif tp == 'm':
      # find the first three-dot, and start the 2nd loop, in which, the
      # three-dots will be ignored
      k = 0
      for k in range(lx):
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
          if p[-(x + o)] == '...':
            o += 1
          elif p[-(x + o)] != s[-x]:
            o -= 1
          else:
            x += 1
    elif tp == 'r':
      # SCI should be longer than pattern
#      print 'l_s=%d,l_p=%d' % (len(s),len(p))
      if len(s) + 1 < len(p):
        r = False
      else:
        for k in range(lx):
          if p[k] == '...':
            pass
          elif p[k] != s[k]:
            r = False
            break
    elif tp == 'n':
      if len(s) == len(p):
        for k in range(lx):
          if p[k] != s[k]:
            r = False
            break

    return r

  def get(self, item=None):
    return self.opts['pattern'], self.opts['version-selector']

  def dump(self):
    li = 'element'
    # scope
    if self.opts['-file']:
      li += ' -file'
    elif self.opts['-dir']:
      li += ' -directory'
    elif self.opts.has_key('-elftype'):
      li += ' -elf ' + self.opts['-elftype']
    # pattern
    li += ' ' + self.opts.get('pattern', '')
    # version-selector
    li += ' ' + self.opts.get('version-selector', '')
    # optional clause
    li += ' ' + self.opts.get('-time', '')

    li = li.replace('   ', ' ')
    li = li.replace('  ', ' ')
    li = li.rstrip()

    return li

  def getRepository(self):
    return self.opts.get('pattern', None)

# mkbranch branch-type-name [-override]
class MkBranchRule(ConfigspecRule):
  def __init__(self, line, rule, branch_name):
    error = None
    opts = dict({'-override' : False})
    s = rule.split()

    k = 1 # mkbranch
    if k < len(s):
      opts['branch-type-name'] = s[k]
      k += 1
    else:
      error = 'branch-type-name is missed'

    if k < len(s):
      if s[k] == '-override':
        opts['-override'] = True
        k += 1

    if k < len(s):
      error = 'Unknown parameter in line'
    else:
      branch_name.append(s[k], opts['-override'])

    ConfigspecRule.__init__(self, 'B', line, rule, error, k, opts)

  def dump(self):
    li = 'mkbranch'
    li += ' ' + self.opts.get('branch-type-name', '')
    li += ' ' + self.opts.get('-override')

    li = li.replace('  ', ' ')
    li = li.rstrip()

    return li

# end mkbranch mkbranch-type-name
class EndMkbranchRule(ConfigspecRule):
  def __init__(self, line, rule, branch_name):
    error = None
    opts = dict()
    s = rule.split()

    k = 2 # end branch
    if len(branch_name) == 0:
      error = 'no mkbranch defined before'
    elif k < len(s):
      opts['branch-type-name'] = s[k]
      if s[k] != branch_name[-1][0]:
        error = 'branch-type-name "%s" mismatch last branch "%s"' % (s[k], branch_name[-1][0])
      else:
        branch_name.pop(-1)
      k += 1

    if k < len(s):
      error = 'Unknown parameter in line'

    ConfigspecRule.__init__(self, 'b', line, rule, error, k, opts)

def dump(self):
  li = 'end mkbranch'
  li += ' ' + self.opts.get('branch-type-name', '')
  li = li.rstrip()

  return li

# time date-time
class TimeRule(ConfigspecRule):
  def __init__(self, line, rule, date_time):
    error = None
    opts = dict()
    is_file = is_dir = is_elf = False
    s = rule.split()

    k = 1 # time
    if k < len(s):
      opts['date-time'] = s[k]
      date_time.append(s[k])
      k += 1
    else:
      error = 'date-time is missed'

    if k < len(s):
      error = 'Unknown parameter in line'

    ConfigspecRule.__init__(self, 'T', line, rule, error, k, opts)

  def dump(self):
    li = 'time'
    li += ' ' + self.opts.get('date-time', '')
    li = li.rstrip()

    return li

# end time [date-time]
class EndTimeRule(ConfigspecRule):
  def __init__(self, line, rule, date_time):
    error = None
    opts = dict()
    s = rule.split()

    k = 2 # end time
    if len(date_time) == 0:
      error = 'no time rule used before'
    elif k < len(s):
      opts['date-time'] = s[k]
      if s[k] != date_time[-1]:
        error = 'date-time "%s" mismatch last time "%s"' % (s[k], date_time[-1])
      else:
        date_time.pop(-1)
      k += 1

    if k < len(s):
      error = 'Unknown parameter in line'

    ConfigspecRule.__init__(self, 't', line, rule, error, k, opts)

  def dump(self):
    li = 'end time'
    li += ' ' + self.opts.get('date-time', '')
    li = li.rstrip()

    return li

# include config-spec-pname
class IncludeRule(ConfigspecRule):
  def __init__(self, line, rule, branch_name, date_time):
    error = None
    opts = dict()
    s = rule.split()

    k = 1 # include
    if k < len(s):
      opts['config-spec-pname'] = s[k]
      k += 1

    if k < len(s):
      error = 'Unknown parameter in line'

    # FIXME: implement the include rule here ...
    ConfigspecRule.__init__(self, 'I', line, rule, error, k, opts)

  def dump(self):
    li = 'include'
    li += ' ' + self.opts.get('config-spec-pname', '')
    li = li.rstrip()

    return li

# load pname
class LoadRule(ConfigspecRule):
  def __init__(self, line, rule):
    error = None
    opts = dict()
    s = rule.split()

    k = 1 # load
    if k < len(s):
      opts['pname'] = s[k]
      k += 1

    if k < len(s):
      error = 'Unknown parameter in line'

    ConfigspecRule.__init__(self, 'L', line, rule, error, k, opts)

  def dump(self):
    li = 'load'
    li += ' ' + self.opts.get('pname', '')
    li = li.rstrip()

    return li

  def getRepository(self):
    return self.opts.get('pname', None)

class Configspec:
  def __init__ (self, configspec='', configspec_file=''):
    lines = configspec.split('\n')
    self.err = self.parse(lines)

  def error (self):
    return self.err

  def parse (self, lines):
    date_time = list()
    branch_name = list()

    self.parsed_lines = list()
    for k, lo in enumerate(lines):
      #print "Line %d: %s" % (k, lo)
      if lo.find('#') > -1: lo = lo[:lo.find('#')]
      for li in lo.split(';'):
        li = li.strip()

        if len(li) == 0 or li.startswith('#'):
          continue

        lz = li.replace('\t', ' ').split()
        #print 'lz=', lz, 'li=', li
        #= element
        if lz[0] == 'element':
          rp = ElementRule(k, lo, branch_name, date_time)
        #= load pname (for snapshot views)
        elif lz[0] == 'load':
          rp = LoadRule(k, lo)
        #= mkbranch branch-type-name [-override]
        elif lz[0] == 'mkbranch':
          rp = MkBranchRule(k, lo, branch_name)
        #= time date-time
        elif lz[0] == 'time':
          rp = TimeRule(k, lo, date_time)
        #= end time [date-time]
        elif len(lz) > 1 and lz[0] == 'end' and lz[1] == 'time':
          rp = EndTimeRule(k, lo, date_time)
        #= end mkbranch [branch-type-name]
        elif len(lz) > 1 and lz[0] == 'end' and lz[1] == 'branch':
          rp = MkBranchRule(k, lo, branch_name)
        #= include config-spec-pname
        elif lz[0] == 'include':
          rp = IncludeRule(k, lo, branch_name, date_time)
        else:
          rp = Error(k, lo)

        if rp.error:
          return 'Line %d: Error - %s' % (rp.line, rp.error)

        self.parsed_lines.append(rp)

    return None

  def match(self, root, sci, prefix):
    ret = list()

    if root.endswith('/'):
      root = root[:-1]

    sci = sci.replace(root, prefix).replace('\\', '/')
    for item in self.parsed_lines:
      if item.match(sci):
        ret.append(item)

    if len(ret):
      return ret
    else:
      return None

  def get(self, c, sci):
    return c.get(sci)

  def getRepositories(self):
    pnames = list()

    for item in self.parsed_lines:
        repo = item.getRepository()
        if repo and (repo not in pnames):
            pnames.append(repo)

    return pnames

if __name__ == '__main__':
  cs = '''
element * CHECKEDOUT
element /vobs/package214/integration/... INTEGRATION-1.0
element /vobs/project183/vyp633/...      VYP633-1.0
element * /main/LATEST'''

  pcs = Configspec(cs)
  mlist = pcs.match('E:\z_vyp623_dev', 'E:\z_vyp623_dev/project183', '/vobs')
  print "OUTPUT (%d) RULES: " % len(mlist)
  print "--------------------------"
  for rule in mlist:
      print rule.dump()
