
import json
import copy
import string

PACKAGE_NAME        = 'name'
PACKAGE_LOCATION    = 'location'
PACKAGE_STATUS      = 'status'
PACKAGE_DESCRIPTION = 'description'
PACKAGE_COMMENT     = 'comment'
PACKAGE_SUBPROJECT  = 'subproject'

LEGAL_CHARACTERS = string.ascii_letters + string.digits + '_.'

def __isLegalName(strp):
    return strp.translate(None, LEGAL_CHARACTERS) == ''

def _parseTextFormat(text):
    ret = dict()

    comment = ''
    for li in text.split( '\n' ):
        li = li.strip()

        if li.startswith( '#' ):
            k = 1
            while k < len(li):
                if li[k] != '#': break
                k += 1

            comment += li[k:]
            continue

        a = li.strip().split()
        if len(a) > 1:
            lr = dict()
            if not __isLegalName(a[0]):
                raise Exception('Wrong package name %s' % a[0])

            lr[PACKAGE_NAME]     = a[0]
            lr[PACKAGE_LOCATION] = a[1]
            if len(a) > 2 and a[2] == 'deprecated':
                lr[PACKAGE_STATUS] = 'deprecated'
            else:
                lr[PACKAGE_STATUS] = 'normal'

            if len(comment) > 0:
                lr[PACKAGE_DESCRIPTION] = comment

            ret[a[0]] = lr

        comment = ''

    return ret

def __copyKeyValues(fr, to=None):
    if to is None:
        to = dict()

    for key in (PACKAGE_NAME, PACKAGE_LOCATION, PACKAGE_DESCRIPTION,
                PACKAGE_COMMENT, PACKAGE_STATUS):
        if fr.has_key(key):
            to[key] = fr[key]

    return to

def _parseJsonFormat(text):
    ret = dict()
    listp = json.loads(text)
    for d in listp or list():
        if isinstance(d, dict):
            if isinstance(d.get(PACKAGE_SUBPROJECT), (list, tuple)):
                for lo in d.get(PACKAGE_SUBPROJECT):
                    la = __copyKeyValues(d)
                    __copyKeyValues(lo, la)
                    ret[la.get(PACKAGE_NAME)] = la
            elif isinstance(d.get(PACKAGE_NAME), (list, tuple)):
                for name in d.get(PACKAGE_NAME):
                    la = __copyKeyValues(d)
                    la[PACKAGE_NAME] = name
                    ret[name] = la
            elif d.has_key(PACKAGE_NAME):
                ret[d[PACKAGE_NAME]] = __copyKeyValues(d)


    return ret

def parse(context):
    try:
        ret = _parseJsonFormat(context)
    except Exception, e:
        #print 'JSON FORMAT:', e
        try:
            ret = _parseTextFormat(context)
        except Exception, e:
        #    print 'TEXT FORMAT:', e
            ret = dict()

    return ret

if __name__ == '__main__':
    import sys
    import pprint

    sys.path.append('platform')
    import wb_read_file

    jso = wb_read_file.readFile("d:/repo.lst")
    pprint.pprint(parse(jso))
