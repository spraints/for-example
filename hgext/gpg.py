# GnuPG signing extension for Mercurial
#
# Copyright 2005, 2006 Benoit Boissinot <benoit.boissinot@ens-lyon.org>
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.

import os, tempfile, binascii
from mercurial import util
from mercurial import node as hgnode
from mercurial.i18n import gettext as _

class gpg:
    def __init__(self, path, key=None):
        self.path = path
        self.key = (key and " --local-user \"%s\"" % key) or ""

    def sign(self, data):
        gpgcmd = "%s --sign --detach-sign%s" % (self.path, self.key)
        return util.filter(data, gpgcmd)

    def verify(self, data, sig):
        """ returns of the good and bad signatures"""
        try:
            # create temporary files
            fd, sigfile = tempfile.mkstemp(prefix="hggpgsig")
            fp = os.fdopen(fd, 'wb')
            fp.write(sig)
            fp.close()
            fd, datafile = tempfile.mkstemp(prefix="hggpgdata")
            fp = os.fdopen(fd, 'wb')
            fp.write(data)
            fp.close()
            gpgcmd = ("%s --logger-fd 1 --status-fd 1 --verify "
                      "\"%s\" \"%s\"" % (self.path, sigfile, datafile))
            ret = util.filter("", gpgcmd)
        except:
            for f in (sigfile, datafile):
                try:
                    if f: os.unlink(f)
                except: pass
            raise
        keys = []
        key, fingerprint = None, None
        err = ""
        for l in ret.splitlines():
            # see DETAILS in the gnupg documentation
            # filter the logger output
            if not l.startswith("[GNUPG:]"):
                continue
            l = l[9:]
            if l.startswith("ERRSIG"):
                err = _("error while verifying signature")
                break
            elif l.startswith("VALIDSIG"):
                # fingerprint of the primary key
                fingerprint = l.split()[10]
            elif (l.startswith("GOODSIG") or
                  l.startswith("EXPSIG") or
                  l.startswith("EXPKEYSIG") or
                  l.startswith("BADSIG")):
                if key is not None:
                    keys.append(key + [fingerprint])
                key = l.split(" ", 2)
                fingerprint = None
        if err:
            return err, []
        if key is not None:
            keys.append(key + [fingerprint])
        return err, keys

def newgpg(ui, **opts):
    """create a new gpg instance"""
    gpgpath = ui.config("gpg", "cmd", "gpg")
    gpgkey = opts.get('key')
    if not gpgkey:
        gpgkey = ui.config("gpg", "key", None)
    return gpg(gpgpath, gpgkey)

def sigwalk(repo):
    """
    walk over every sigs, yields a couple
    ((node, version, sig), (filename, linenumber))
    """
    def parsefile(fileiter, context):
        ln = 1
        for l in fileiter:
            if not l:
                continue
            yield (l.split(" ", 2), (context, ln))
            ln +=1

    fl = repo.file(".hgsigs")
    h = fl.heads()
    h.reverse()
    # read the heads
    for r in h:
        fn = ".hgsigs|%s" % hgnode.short(r)
        for item in parsefile(fl.read(r).splitlines(), fn):
            yield item
    try:
        # read local signatures
        fn = "localsigs"
        for item in parsefile(repo.opener(fn), fn):
            yield item
    except IOError:
        pass

def getkeys(ui, repo, mygpg, sigdata, context):
    """get the keys who signed a data"""
    fn, ln = context
    node, version, sig = sigdata
    prefix = "%s:%d" % (fn, ln)
    node = hgnode.bin(node)

    data = node2txt(repo, node, version)
    sig = binascii.a2b_base64(sig)
    err, keys = mygpg.verify(data, sig)
    if err:
        ui.warn("%s:%d %s\n" % (fn, ln , err))
        return None

    validkeys = []
    # warn for expired key and/or sigs
    for key in keys:
        if key[0] == "BADSIG":
            ui.write(_("%s Bad signature from \"%s\"\n") % (prefix, key[2]))
            continue
        if key[0] == "EXPSIG":
            ui.write(_("%s Note: Signature has expired"
                       " (signed by: \"%s\")\n") % (prefix, key[2]))
        elif key[0] == "EXPKEYSIG":
            ui.write(_("%s Note: This key has expired"
                       " (signed by: \"%s\")\n") % (prefix, key[2]))
        validkeys.append((key[1], key[2], key[3]))
    return validkeys

def sigs(ui, repo):
    """list signed changesets"""
    mygpg = newgpg(ui)
    revs = {}

    for data, context in sigwalk(repo):
        node, version, sig = data
        fn, ln = context
        try:
            n = repo.lookup(node)
        except KeyError:
            ui.warn(_("%s:%d node does not exist\n") % (fn, ln))
            continue
        r = repo.changelog.rev(n)
        keys = getkeys(ui, repo, mygpg, data, context)
        if not keys:
            continue
        revs.setdefault(r, [])
        revs[r].extend(keys)
    nodes = list(revs)
    nodes.reverse()
    for r in nodes:
        for k in revs[r]:
            r = "%5d:%s" % (r, hgnode.hex(repo.changelog.node(r)))
            ui.write("%-30s %s\n" % (keystr(ui, k), r))

def check(ui, repo, rev):
    """verify all the signatures there may be for a particular revision"""
    mygpg = newgpg(ui)
    rev = repo.lookup(rev)
    hexrev = hgnode.hex(rev)
    keys = []

    for data, context in sigwalk(repo):
        node, version, sig = data
        if node == hexrev:
            k = getkeys(ui, repo, mygpg, data, context)
            if k:
                keys.extend(k)

    if not keys:
        ui.write(_("No valid signature for %s\n") % hgnode.short(rev))
        return

    # print summary
    ui.write("%s is signed by:\n" % hgnode.short(rev))
    for key in keys:
        ui.write(" %s\n" % keystr(ui, key))

def keystr(ui, key):
    """associate a string to a key (username, comment)"""
    keyid, user, fingerprint = key
    comment = ui.config("gpg", fingerprint, None)
    if comment:
        return "%s (%s)" % (user, comment)
    else:
        return user

def sign(ui, repo, *revs, **opts):
    """add a signature for the current tip or a given revision"""
    mygpg = newgpg(ui, **opts)
    sigver = "0"
    sigmessage = ""
    if revs:
        nodes = [repo.lookup(n) for n in revs]
    else:
        nodes = [repo.changelog.tip()]

    for n in nodes:
        hexnode = hgnode.hex(n)
        ui.write("Signing %d:%s\n" % (repo.changelog.rev(n),
                                      hgnode.short(n)))
        # build data
        data = node2txt(repo, n, sigver)
        sig = mygpg.sign(data)
        if not sig:
            raise util.Abort(_("Error while signing"))
        sig = binascii.b2a_base64(sig)
        sig = sig.replace("\n", "")
        sigmessage += "%s %s %s\n" % (hexnode, sigver, sig)

    # write it
    if opts['local']:
        repo.opener("localsigs", "ab").write(sigmessage)
        return

    for x in repo.changes():
        if ".hgsigs" in x and not opts["force"]:
            raise util.Abort(_("working copy of .hgsigs is changed "
                               "(please commit .hgsigs manually "
                               "or use --force)"))

    repo.wfile(".hgsigs", "ab").write(sigmessage)

    if repo.dirstate.state(".hgsigs") == '?':
        repo.add([".hgsigs"])

    if opts["no_commit"]:
        return

    message = opts['message']
    if not message:
        message = "\n".join([_("Added signature for changeset %s")
                             % hgnode.hex(n)
                             for n in nodes])
    try:
        repo.commit([".hgsigs"], message, opts['user'], opts['date'])
    except ValueError, inst:
        raise util.Abort(str(inst))

def node2txt(repo, node, ver):
    """map a manifest into some text"""
    if ver == "0":
        return "%s\n" % hgnode.hex(node)
    else:
        util.Abort(_("unknown signature version"))

cmdtable = {
    "sign":
        (sign,
         [('l', 'local', None, _("make the signature local")),
          ('f', 'force', None, _("sign even if the sigfile is modified")),
          ('', 'no-commit', None, _("do not commit the sigfile after signing")),
          ('m', 'message', "", _("commit message")),
          ('d', 'date', "", _("date code")),
          ('u', 'user', "", _("user")),
          ('k', 'key', "", _("the key id to sign with"))],
         _("hg sign [OPTION]... REVISIONS")),
    "sigcheck": (check, [], _('hg sigcheck REVISION')),
    "sigs": (sigs, [], _('hg sigs')),
}

