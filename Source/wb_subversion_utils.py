'''
 ====================================================================
 Copyright (c) 2003-2009 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_subversion_utils.py

'''
import pysvn
import time
import types
import locale
import wx
import wb_exceptions

class svn_version_info:
    #
    # Keep infos about the features of the available pysvn version
    #
    def __init__(self):
        self.notify_action_has_failed_lock = hasattr( pysvn.wc_notify_action, 'failed_lock' )
        self.has_depth = hasattr( pysvn, 'depth' )
        self.notify_action_has_property_events = hasattr( pysvn.wc_notify_action, 'property_added' )

version_info = svn_version_info()

def fmtDateTime( val ):
    encoding = locale.getlocale()[1]
    if type( val ) == types.FloatType:
        val = time.localtime( val )

    return time.strftime( '%d-%b-%Y %H:%M:%S', val ).decode( encoding )

wc_status_kind_map = {
pysvn.wc_status_kind.missing:       '?',
pysvn.wc_status_kind.added:         'A',
pysvn.wc_status_kind.conflicted:    'C',
pysvn.wc_status_kind.deleted:       'D',
pysvn.wc_status_kind.external:      'X',
pysvn.wc_status_kind.ignored:       'I',
pysvn.wc_status_kind.incomplete:    '!',
pysvn.wc_status_kind.missing:       '!',
pysvn.wc_status_kind.merged:        'G',
pysvn.wc_status_kind.modified:      'M',
pysvn.wc_status_kind.none:          ' ',
pysvn.wc_status_kind.normal:        ' ',
pysvn.wc_status_kind.obstructed:    '~',
pysvn.wc_status_kind.replaced:      'R',
pysvn.wc_status_kind.unversioned:   '?',
}

# lookup the status and see if it means the file will be checked in
wc_status_checkin_map = {
pysvn.wc_status_kind.missing:       False,
pysvn.wc_status_kind.added:         True,
pysvn.wc_status_kind.conflicted:    True,       # allow user to see the conflicted file
pysvn.wc_status_kind.deleted:       True,
pysvn.wc_status_kind.external:      False,
pysvn.wc_status_kind.ignored:       False,
pysvn.wc_status_kind.incomplete:    False,
pysvn.wc_status_kind.missing:       False,
pysvn.wc_status_kind.merged:        True,
pysvn.wc_status_kind.modified:      True,
pysvn.wc_status_kind.none:          False,
pysvn.wc_status_kind.normal:        False,
pysvn.wc_status_kind.obstructed:    False,
pysvn.wc_status_kind.replaced:      True,
pysvn.wc_status_kind.unversioned:   False,
}

# return a value used to sort by status
#  1-10 - text status
# 11-20 - prop status
# 21-30 - other status

wc_status_kind_text_sort_map = {
# need use to update
pysvn.wc_status_kind.missing:       1,
pysvn.wc_status_kind.incomplete:    1,
pysvn.wc_status_kind.obstructed:    1,

# user needs to sort this one out
pysvn.wc_status_kind.conflicted:    2,

# need user to checkin
pysvn.wc_status_kind.deleted:       3,
pysvn.wc_status_kind.added:         4,
pysvn.wc_status_kind.modified:      4,

# other controlled files
pysvn.wc_status_kind.normal:        -21,
pysvn.wc_status_kind.external:      -21,

# uncontrolled but interesting files
pysvn.wc_status_kind.unversioned:   -22,

# uncontrolled but uninteresting files
pysvn.wc_status_kind.ignored:       -23,

# svn will not return these as the status of a file only of a change in a file
pysvn.wc_status_kind.replaced:      0,
pysvn.wc_status_kind.none:          0,
pysvn.wc_status_kind.merged:        0,
}

prop_sort_offset = 10

wc_notify_action_map = {
    pysvn.wc_notify_action.add: 'A',
    pysvn.wc_notify_action.commit_added: 'A',
    pysvn.wc_notify_action.commit_deleted: 'D',
    pysvn.wc_notify_action.commit_modified: 'M',
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'R',
    pysvn.wc_notify_action.copy: 'c',
    pysvn.wc_notify_action.delete: 'D',
    pysvn.wc_notify_action.failed_revert: 'F',
    pysvn.wc_notify_action.resolved: 'R',
    pysvn.wc_notify_action.restore: 'R',
    pysvn.wc_notify_action.revert: 'R',
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external: 'E',
    pysvn.wc_notify_action.update_add: 'A',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'D',
    pysvn.wc_notify_action.update_external: 'E',
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.annotate_revision: 'a',
    }

if version_info.notify_action_has_failed_lock:
    wc_notify_action_map[ pysvn.wc_notify_action.failed_lock ] = 'lock failed'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_unlock ] = 'unlock failed'
    wc_notify_action_map[ pysvn.wc_notify_action.locked ] = 'Locked'
    wc_notify_action_map[ pysvn.wc_notify_action.unlocked ] = 'Unlocked'

if version_info.notify_action_has_property_events:
    wc_notify_action_map[ pysvn.wc_notify_action.property_added ] = '_A'
    wc_notify_action_map[ pysvn.wc_notify_action.property_modified ] = '_M'
    wc_notify_action_map[ pysvn.wc_notify_action.property_deleted ] = '_D'
    wc_notify_action_map[ pysvn.wc_notify_action.property_deleted_nonexistent ] = 'property_deleted_nonexistent'
    wc_notify_action_map[ pysvn.wc_notify_action.revprop_set ] = 'revprop_set'
    wc_notify_action_map[ pysvn.wc_notify_action.revprop_deleted ] = 'revprop_deleted'
    wc_notify_action_map[ pysvn.wc_notify_action.merge_completed ] = 'merge_completed'
    wc_notify_action_map[ pysvn.wc_notify_action.tree_conflict ] = 'tree_conflict'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_external ] = 'failed_external'

wc_notify_type_map = {
    pysvn.wc_notify_action.add: 'A',
    pysvn.wc_notify_action.commit_added: 'C',
    pysvn.wc_notify_action.commit_deleted: 'C',
    pysvn.wc_notify_action.commit_modified: 'C',
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'C',
    pysvn.wc_notify_action.copy: 'A',
    pysvn.wc_notify_action.delete: 'A',
    pysvn.wc_notify_action.failed_revert: 'A',
    pysvn.wc_notify_action.resolved: 'A',
    pysvn.wc_notify_action.restore: 'A',
    pysvn.wc_notify_action.revert: 'A',
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external: 'A',
    pysvn.wc_notify_action.update_add: 'U',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'U',
    pysvn.wc_notify_action.update_external: 'U',
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.annotate_revision: 'A',
    }

if version_info.notify_action_has_failed_lock:
    wc_notify_type_map[ pysvn.wc_notify_action.failed_lock ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.failed_unlock ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.locked ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.unlocked ] = None

if version_info.notify_action_has_property_events:
    wc_notify_type_map[ pysvn.wc_notify_action.property_added ] = 'A'
    wc_notify_type_map[ pysvn.wc_notify_action.property_modified ] = 'M'
    wc_notify_type_map[ pysvn.wc_notify_action.property_deleted ] = 'D'
    wc_notify_type_map[ pysvn.wc_notify_action.property_deleted_nonexistent ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.revprop_set ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.revprop_deleted ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.merge_completed ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.tree_conflict ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.failed_external ] = None


#
#    format the concise status from file
#
def _status_format( file ):
    if file.entry is None:
        return ''

    text_code = wc_status_kind_map[ file.text_status ]
    prop_code = wc_status_kind_map[ file.prop_status ]
    if text_code == ' ' and prop_code != ' ':
        text_code = '_'
    if (file.is_locked or file.is_copied or file.is_switched) and prop_code == ' ':
        prop_code = '_'

    lock_state = ' '
    if file.entry is not None and hasattr( file.entry, 'lock_token' ):
        if file.entry.lock_token is not None:
            lock_state = 'K'

    state = '%s%s%s%s%s%s' % (text_code, prop_code,
            ' L'[ file.is_locked ],
            ' +'[ file.is_copied ],
            ' S'[ file.is_switched ],
            lock_state)

    return state.strip()

def populateMenu( menu, contents ):
    for details in contents:
        if len(details) == 3:
            type, id, name = details
            cond = True
        else:
            type, id, name, cond = details

        if type == '-':
            if cond:
                menu.AppendSeparator()
        elif type == 'x':
            menu.AppendCheckItem( id, name )
            menu.Enable( id, cond )
        elif type == 'o':
            menu.AppendRadioItem( id, name )
            menu.Enable( id, cond )
        elif type == '':
            menu.Append( id, name )
            menu.Enable( id, cond )
        elif type == '>':
            # sub menu in the list in id
            menu.AppendMenu( id, name, populateMenu( wx.Menu(), cond ) )
        else:
            raise wb_exceptions.InternalError(
                'Unknown populateMenu contents (%s,%s,%s,%s)' %
                    (repr(type),repr(id),repr(name),repr(cond)) )
    return menu

def by_path( a, b ):
    return cmp( a.path, b.path )

