# acl.py - changeset access control for mercurial
#
# Copyright 2006 Vadim Gelfer <vadim.gelfer@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''hooks for controlling repository access

This hook makes it possible to allow or deny write access to portions
of a repository when receiving incoming changesets via pretxnchangegroup and
pretxncommit.

The authorization is matched based on the local user name on the
system where the hook runs, and not the committer of the original
changeset (since the latter is merely informative).

The acl hook is best used along with a restricted shell like hgsh,
preventing authenticating users from doing anything other than
pushing or pulling. The hook is not safe to use if users have
interactive shell access, as they can then disable the hook.
Nor is it safe if remote users share an account, because then there
is no way to distinguish them.

The deny list is checked before the allow list.

The allow and deny sections take key-value pairs, having a subtree pattern
as key (with a glob syntax by default). The corresponding value can be either:

1) an asterisk, to match everyone;
2) a comma-separated list containing users and groups.

Group names must be prefixed with an ``@`` symbol.
Specifying a group name has the same effect as specifying all the users in
that group.

To use this hook, configure the acl extension in your hgrc like this::

  [extensions]
  acl =

  [hooks]

  # Use this if you want to check access restrictions at commit time.
  pretxncommit.acl = python:hgext.acl.hook
  
  # Use this if you want to check access restrictions for pull, push, bundle
  # and serve.
  pretxnchangegroup.acl = python:hgext.acl.hook

  [acl]
  # Check whether the source of incoming changes is in this list where
  # "serve" == ssh or http, and "push", "pull" and "bundle" are the
  # corresponding hg commands.
  sources = serve

  [acl.deny]
  # This list is checked first. If a match is found, 'acl.allow' will not be
  # checked. All users are granted access if acl.deny is not present.
  # Format for both lists: glob pattern = user, ..., @group, ...

  # To match everyone, use an asterisk for the user:
  # my/glob/pattern = *

  # user6 will not have write access to any file:
  ** = user6

  # Group "hg-denied" will not have write access to any file:
  ** = @hg-denied

  # Nobody will be able to change "DONT-TOUCH-THIS.txt", despite everyone being
  # able to change all other files. See below.
  src/main/resources/DONT-TOUCH-THIS.txt = *

  [acl.allow]
  # if acl.allow not present, all users allowed by default
  # empty acl.allow = no users allowed

  # User "doc_writer" has write access to any file under the "docs" folder:
  docs/** = doc_writer

  # User "jack" and group "designers" have write access to any file under the
  # "images" folder:
  images/** = jack, @designers

  # Everyone (except for "user6" - see "acl.deny" above) will have write access
  # to any file under the "resources" folder (except for 1 file. See "acl.deny"):
  src/main/resources/** = *

  .hgtags = release_engineer

'''

from mercurial.i18n import _
from mercurial import util, match
import getpass, urllib, grp

def _getusers(group):
    return grp.getgrnam(group).gr_mem

def _usermatch(user, usersorgroups):

    if usersorgroups == '*':
        return True

    for ug in usersorgroups.replace(',', ' ').split():
        if user == ug or ug.find('@') == 0 and user in _getusers(ug[1:]):
            return True

    return False

def buildmatch(ui, repo, user, key):
    '''return tuple of (match function, list enabled).'''
    if not ui.has_section(key):
        ui.debug('acl: %s not enabled\n' % key)
        return None

    pats = [pat for pat, users in ui.configitems(key)
            if _usermatch(user, users)]
    ui.debug('acl: %s enabled, %d entries for user %s\n' %
             (key, len(pats), user))
    if pats:
        return match.match(repo.root, '', pats)
    return match.exact(repo.root, '', [])


def hook(ui, repo, hooktype, node=None, source=None, **kwargs):
    if hooktype not in ['pretxnchangegroup', 'pretxncommit']:
        raise util.Abort(_('config error - hook type "%s" cannot stop '
                           'incoming changesets nor commits') % hooktype)
    if (hooktype == 'pretxnchangegroup' and
        source not in ui.config('acl', 'sources', 'serve').split()):
        ui.debug('acl: changes have source "%s" - skipping\n' % source)
        return

    user = None
    if source == 'serve' and 'url' in kwargs:
        url = kwargs['url'].split(':')
        if url[0] == 'remote' and url[1].startswith('http'):
            user = urllib.unquote(url[3])

    if user is None:
        user = getpass.getuser()

    cfg = ui.config('acl', 'config')
    if cfg:
        ui.readconfig(cfg, sections = ['acl.allow', 'acl.deny'])
    allow = buildmatch(ui, repo, user, 'acl.allow')
    deny = buildmatch(ui, repo, user, 'acl.deny')

    for rev in xrange(repo[node], len(repo)):
        ctx = repo[rev]
        for f in ctx.files():
            if deny and deny(f):
                ui.debug('acl: user %s denied on %s\n' % (user, f))
                raise util.Abort(_('acl: access denied for changeset %s') % ctx)
            if allow and not allow(f):
                ui.debug('acl: user %s not allowed on %s\n' % (user, f))
                raise util.Abort(_('acl: access denied for changeset %s') % ctx)
        ui.debug('acl: allowing changeset %s\n' % ctx)
