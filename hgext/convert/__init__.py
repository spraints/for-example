# convert.py Foreign SCM converter
#
# Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.

import sys, os, zlib, sha, time, re, locale, socket
from mercurial import hg, ui, util, commands, repo

commands.norepo += " convert"

class NoRepo(Exception): pass

class commit(object):
    def __init__(self, **parts):
        for x in "author date desc parents".split():
            if not x in parts:
                raise util.Abort("commit missing field %s\n" % x)
        self.__dict__.update(parts)

def recode(s):
    try:
        return s.decode("utf-8").encode("utf-8")
    except:
        try:
            return s.decode("latin-1").encode("utf-8")
        except:
            return s.decode("utf-8", "replace").encode("utf-8")

class converter_source(object):
    """Conversion source interface"""

    def __init__(self, ui, path):
        """Initialize conversion source (or raise NoRepo("message")
        exception if path is not a valid repository)"""
        raise NotImplementedError()

    def getheads(self):
        """Return a list of this repository's heads"""
        raise NotImplementedError()

    def getfile(self, name, rev):
        """Return file contents as a string"""
        raise NotImplementedError()

    def getmode(self, name, rev):
        """Return file mode, eg. '', 'x', or 'l'"""
        raise NotImplementedError()

    def getchanges(self, version):
        """Return sorted list of (filename, id) tuples for all files changed in rev.

        id just tells us which revision to return in getfile(), e.g. in
        git it's an object hash."""
        raise NotImplementedError()

    def getcommit(self, version):
        """Return the commit object for version"""
        raise NotImplementedError()

    def gettags(self):
        """Return the tags as a dictionary of name: revision"""
        raise NotImplementedError()

class converter_sink(object):
    """Conversion sink (target) interface"""

    def __init__(self, ui, path):
        """Initialize conversion sink (or raise NoRepo("message")
        exception if path is not a valid repository)"""
        raise NotImplementedError()

    def getheads(self):
        """Return a list of this repository's heads"""
        raise NotImplementedError()

    def mapfile(self):
        """Path to a file that will contain lines
        source_rev_id sink_rev_id
        mapping equivalent revision identifiers for each system."""
        raise NotImplementedError()

    def putfile(self, f, e, data):
        """Put file for next putcommit().
        f: path to file
        e: '', 'x', or 'l' (regular file, executable, or symlink)
        data: file contents"""
        raise NotImplementedError()

    def delfile(self, f):
        """Delete file for next putcommit().
        f: path to file"""
        raise NotImplementedError()

    def putcommit(self, files, parents, commit):
        """Create a revision with all changed files listed in 'files'
        and having listed parents. 'commit' is a commit object containing
        at a minimum the author, date, and message for this changeset.
        Called after putfile() and delfile() calls. Note that the sink
        repository is not told to update itself to a particular revision
        (or even what that revision would be) before it receives the
        file data."""
        raise NotImplementedError()

    def puttags(self, tags):
        """Put tags into sink.
        tags: {tagname: sink_rev_id, ...}"""
        raise NotImplementedError()


# CVS conversion code inspired by hg-cvs-import and git-cvsimport
class convert_cvs(converter_source):
    def __init__(self, ui, path):
        self.path = path
        self.ui = ui
        cvs = os.path.join(path, "CVS")
        if not os.path.exists(cvs):
            raise NoRepo("couldn't open CVS repo %s" % path)

        self.changeset = {}
        self.files = {}
        self.tags = {}
        self.lastbranch = {}
        self.parent = {}
        self.socket = None
        self.cvsroot = file(os.path.join(cvs, "Root")).read()[:-1]
        self.cvsrepo = file(os.path.join(cvs, "Repository")).read()[:-1]
        self.encoding = locale.getpreferredencoding()
        self._parse()
        self._connect()

    def _parse(self):
        if self.changeset:
            return

        d = os.getcwd()
        try:
            os.chdir(self.path)
            id = None
            state = 0
            for l in os.popen("cvsps -A -u --cvs-direct -q"):
                if state == 0: # header
                    if l.startswith("PatchSet"):
                        id = l[9:-2]
                    elif l.startswith("Date"):
                        date = util.parsedate(l[6:-1], ["%Y/%m/%d %H:%M:%S"])
                        date = util.datestr(date)
                    elif l.startswith("Branch"):
                        branch = l[8:-1]
                        self.parent[id] = self.lastbranch.get(branch,'bad')
                        self.lastbranch[branch] = id
                    elif l.startswith("Ancestor branch"):
                        ancestor = l[17:-1]
                        self.parent[id] = self.lastbranch[ancestor]
                    elif l.startswith("Author"):
                        author = self.recode(l[8:-1])
                    elif l.startswith("Tag: "):
                        t = l[5:-1].rstrip()
                        if t != "(none)":
                            self.tags[t] = id
                    elif l.startswith("Log:"):
                        state = 1
                        log = ""
                elif state == 1: # log
                    if l == "Members: \n":
                        files = {}
                        log = self.recode(log[:-1])
                        if log.isspace():
                            log = "*** empty log message ***\n"
                        state = 2
                    else:
                        log += l
                elif state == 2:
                    if l == "\n": #
                        state = 0
                        p = [self.parent[id]]
                        if id == "1":
                            p = []
                        if branch == "HEAD":
                            branch = ""
                        c = commit(author=author, date=date, parents=p,
                                   desc=log, branch=branch)
                        self.changeset[id] = c
                        self.files[id] = files
                    else:
                        colon = l.rfind(':')
                        file = l[1:colon]
                        rev = l[colon+1:-2]
                        rev = rev.split("->")[1]
                        files[file] = rev

            self.heads = self.lastbranch.values()
        finally:
            os.chdir(d)

    def _connect(self):
        root = self.cvsroot
        conntype = None
        user, host = None, None
        cmd = ['cvs', 'server']

        self.ui.status("connecting to %s\n" % root)

        if root.startswith(":pserver:"):
            root = root[9:]
            m = re.match(r'(?:(.*?)(?::(.*?))?@)?([^:\/]*)(?::(\d*))?(.*)', root)
            if m:
                conntype = "pserver"
                user, passw, serv, port, root = m.groups()
                if not user:
                    user = "anonymous"
                rr = ":pserver:" + user + "@" + serv + ":" +  root
                if port:
                    rr2, port = "-", int(port)
                else:
                    rr2, port = rr, 2401
                rr += str(port)

                if not passw:
                    passw = "A"
                    pf = open(os.path.join(os.environ["HOME"], ".cvspass"))
                    for l in pf:
                        # :pserver:cvs@mea.tmt.tele.fi:/cvsroot/zmailer Ah<Z
                        m = re.match(r'(/\d+\s+/)?(.*)', l)
                        l = m.group(2)
                        w, p = l.split(' ', 1)
                        if w in [rr, rr2]:
                            passw = p
                            break
                    pf.close()

                sck = socket.socket()
                sck.connect((serv, port))
                sck.send("\n".join(["BEGIN AUTH REQUEST", root, user, passw, "END AUTH REQUEST", ""]))
                if sck.recv(128) != "I LOVE YOU\n":
                    raise NoRepo("CVS pserver authentication failed")

                self.writep = self.readp = sck.makefile('r+')

        if not conntype and root.startswith(":local:"):
            conntype = "local"
            root = root[7:]

        if not conntype:
            # :ext:user@host/home/user/path/to/cvsroot
            if root.startswith(":ext:"):
                root = root[5:]
            m = re.match(r'(?:([^@:/]+)@)?([^:/]+):?(.*)', root)
            if not m:
                conntype = "local"
            else:
                conntype = "rsh"
                user, host, root = m.group(1), m.group(2), m.group(3)

        if conntype != "pserver":
            if conntype == "rsh":
                rsh = os.environ.get("CVS_RSH" or "rsh")
                if user:
                    cmd = [rsh, '-l', user, host] + cmd
                else:
                    cmd = [rsh, host] + cmd

            self.writep, self.readp = os.popen2(cmd)

        self.realroot = root

        self.writep.write("Root %s\n" % root)
        self.writep.write("Valid-responses ok error Valid-requests Mode"
                          " M Mbinary E Checked-in Created Updated"
                          " Merged Removed\n")
        self.writep.write("valid-requests\n")
        self.writep.flush()
        r = self.readp.readline()
        if not r.startswith("Valid-requests"):
            raise util.Abort("server sucks\n")
        if "UseUnchanged" in r:
            self.writep.write("UseUnchanged\n")
            self.writep.flush()
            r = self.readp.readline()

    def getheads(self):
        return self.heads

    def _getfile(self, name, rev):
        if rev.endswith("(DEAD)"):
            raise IOError

        args = ("-N -P -kk -r %s --" % rev).split()
        args.append(os.path.join(self.cvsrepo, name))
        for x in args:
            self.writep.write("Argument %s\n" % x)
        self.writep.write("Directory .\n%s\nco\n" % self.realroot)
        self.writep.flush()

        data = ""
        while 1:
            line = self.readp.readline()
            if line.startswith("Created ") or line.startswith("Updated "):
                self.readp.readline() # path
                self.readp.readline() # entries
                mode = self.readp.readline()[:-1]
                count = int(self.readp.readline()[:-1])
                data = self.readp.read(count)
            elif line.startswith(" "):
                data += line[1:]
            elif line.startswith("M "):
                pass
            elif line.startswith("Mbinary "):
                count = int(self.readp.readline()[:-1])
                data = self.readp.read(count)
            else:
                if line == "ok\n":
                    return (data, "x" in mode and "x" or "")
                elif line.startswith("E "):
                    self.ui.warn("cvs server: %s\n" % line[2:])
                elif line.startswith("Remove"):
                    l = self.readp.readline()
                    l = self.readp.readline()
                    if l != "ok\n":
                        raise util.Abort("unknown CVS response: %s\n" % l)
                else:
                    raise util.Abort("unknown CVS response: %s\n" % line)

    def getfile(self, file, rev):
        data, mode = self._getfile(file, rev)
        self.modecache[(file, rev)] = mode
        return data

    def getmode(self, file, rev):
        return self.modecache[(file, rev)]

    def getchanges(self, rev):
        self.modecache = {}
        files = self.files[rev]
        cl = files.items()
        cl.sort()
        return cl

    def recode(self, text):
        return text.decode(self.encoding, "replace").encode("utf-8")

    def getcommit(self, rev):
        return self.changeset[rev]

    def gettags(self):
        return self.tags

class convert_git(converter_source):
    def __init__(self, ui, path):
        if os.path.isdir(path + "/.git"):
            path += "/.git"
        self.path = path
        self.ui = ui
        if not os.path.exists(path + "/objects"):
            raise NoRepo("couldn't open GIT repo %s" % path)

    def getheads(self):
        fh = os.popen("GIT_DIR=%s git-rev-parse --verify HEAD" % self.path)
        return [fh.read()[:-1]]

    def catfile(self, rev, type):
        if rev == "0" * 40: raise IOError()
        fh = os.popen("GIT_DIR=%s git-cat-file %s %s 2>/dev/null" % (self.path, type, rev))
        return fh.read()

    def getfile(self, name, rev):
        return self.catfile(rev, "blob")

    def getmode(self, name, rev):
        return self.modecache[(name, rev)]

    def getchanges(self, version):
        self.modecache = {}
        fh = os.popen("GIT_DIR=%s git-diff-tree --root -m -r %s" % (self.path, version))
        changes = []
        for l in fh:
            if "\t" not in l: continue
            m, f = l[:-1].split("\t")
            m = m.split()
            h = m[3]
            p = (m[1] == "100755")
            s = (m[1] == "120000")
            self.modecache[(f, h)] = (p and "x") or (s and "l") or ""
            changes.append((f, h))
        return changes

    def getcommit(self, version):
        c = self.catfile(version, "commit") # read the commit hash
        end = c.find("\n\n")
        message = c[end+2:]
        message = recode(message)
        l = c[:end].splitlines()
        manifest = l[0].split()[1]
        parents = []
        for e in l[1:]:
            n,v = e.split(" ", 1)
            if n == "author":
                p = v.split()
                tm, tz = p[-2:]
                author = " ".join(p[:-2])
                if author[0] == "<": author = author[1:-1]
                author = recode(author)
            if n == "committer":
                p = v.split()
                tm, tz = p[-2:]
                committer = " ".join(p[:-2])
                if committer[0] == "<": committer = committer[1:-1]
                committer = recode(committer)
                message += "\ncommitter: %s\n" % committer
            if n == "parent": parents.append(v)

        tzs, tzh, tzm = tz[-5:-4] + "1", tz[-4:-2], tz[-2:]
        tz = -int(tzs) * (int(tzh) * 3600 + int(tzm))
        date = tm + " " + str(tz)

        c = commit(parents=parents, date=date, author=author, desc=message)
        return c

    def gettags(self):
        tags = {}
        fh = os.popen('git-ls-remote --tags "%s" 2>/dev/null' % self.path)
        prefix = 'refs/tags/'
        for line in fh:
            line = line.strip()
            if not line.endswith("^{}"):
                continue
            node, tag = line.split(None, 1)
            if not tag.startswith(prefix):
                continue
            tag = tag[len(prefix):-3]
            tags[tag] = node

        return tags

class convert_mercurial(converter_sink):
    def __init__(self, ui, path):
        self.path = path
        self.ui = ui
        try:
            self.repo = hg.repository(self.ui, path)
        except:
            raise NoRepo("could open hg repo %s" % path)

    def mapfile(self):
        return os.path.join(self.path, ".hg", "shamap")

    def getheads(self):
        h = self.repo.changelog.heads()
        return [ hg.hex(x) for x in h ]

    def putfile(self, f, e, data):
        self.repo.wwrite(f, data, e)
        if self.repo.dirstate.state(f) == '?':
            self.repo.dirstate.update([f], "a")

    def delfile(self, f):
        try:
            os.unlink(self.repo.wjoin(f))
            #self.repo.remove([f])
        except:
            pass

    def putcommit(self, files, parents, commit):
        seen = {}
        pl = []
        for p in parents:
            if p not in seen:
                pl.append(p)
                seen[p] = 1
        parents = pl

        if len(parents) < 2: parents.append("0" * 40)
        if len(parents) < 2: parents.append("0" * 40)
        p2 = parents.pop(0)

        text = commit.desc
        extra = {}
        try:
            extra["branch"] = commit.branch
        except AttributeError:
            pass

        while parents:
            p1 = p2
            p2 = parents.pop(0)
            a = self.repo.rawcommit(files, text, commit.author, commit.date,
                                    hg.bin(p1), hg.bin(p2), extra=extra)
            text = "(octopus merge fixup)\n"
            p2 = hg.hex(self.repo.changelog.tip())

        return p2

    def puttags(self, tags):
        try:
            old = self.repo.wfile(".hgtags").read()
            oldlines = old.splitlines(1)
            oldlines.sort()
        except:
            oldlines = []

        k = tags.keys()
        k.sort()
        newlines = []
        for tag in k:
            newlines.append("%s %s\n" % (tags[tag], tag))

        newlines.sort()

        if newlines != oldlines:
            self.ui.status("updating tags\n")
            f = self.repo.wfile(".hgtags", "w")
            f.write("".join(newlines))
            f.close()
            if not oldlines: self.repo.add([".hgtags"])
            date = "%s 0" % int(time.mktime(time.gmtime()))
            self.repo.rawcommit([".hgtags"], "update tags", "convert-repo",
                                date, self.repo.changelog.tip(), hg.nullid)
            return hg.hex(self.repo.changelog.tip())

converters = [convert_cvs, convert_git, convert_mercurial]

def converter(ui, path):
    if not os.path.isdir(path):
        raise util.Abort("%s: not a directory\n" % path)
    for c in converters:
        try:
            return c(ui, path)
        except NoRepo:
            pass
    raise util.Abort("%s: unknown repository type\n" % path)

class convert(object):
    def __init__(self, ui, source, dest, mapfile, opts):

        self.source = source
        self.dest = dest
        self.ui = ui
        self.mapfile = mapfile
        self.opts = opts
        self.commitcache = {}

        self.map = {}
        try:
            for l in file(self.mapfile):
                sv, dv = l[:-1].split()
                self.map[sv] = dv
        except IOError:
            pass

    def walktree(self, heads):
        visit = heads
        known = {}
        parents = {}
        while visit:
            n = visit.pop(0)
            if n in known or n in self.map: continue
            known[n] = 1
            self.commitcache[n] = self.source.getcommit(n)
            cp = self.commitcache[n].parents
            for p in cp:
                parents.setdefault(n, []).append(p)
                visit.append(p)

        return parents

    def toposort(self, parents):
        visit = parents.keys()
        seen = {}
        children = {}

        while visit:
            n = visit.pop(0)
            if n in seen: continue
            seen[n] = 1
            pc = 0
            if n in parents:
                for p in parents[n]:
                    if p not in self.map: pc += 1
                    visit.append(p)
                    children.setdefault(p, []).append(n)
            if not pc: root = n

        s = []
        removed = {}
        visit = children.keys()
        while visit:
            n = visit.pop(0)
            if n in removed: continue
            dep = 0
            if n in parents:
                for p in parents[n]:
                    if p in self.map: continue
                    if p not in removed:
                        # we're still dependent
                        visit.append(n)
                        dep = 1
                        break

            if not dep:
                # all n's parents are in the list
                removed[n] = 1
                if n not in self.map:
                    s.append(n)
                if n in children:
                    for c in children[n]:
                        visit.insert(0, c)

        if self.opts.get('datesort'):
            depth = {}
            for n in s:
                depth[n] = 0
                pl = [p for p in self.commitcache[n].parents if p not in self.map]
                if pl:
                    depth[n] = max([depth[p] for p in pl]) + 1

            s = [(depth[n], self.commitcache[n].date, n) for n in s]
            s.sort()
            s = [e[2] for e in s]

        return s

    def copy(self, rev):
        c = self.commitcache[rev]
        files = self.source.getchanges(rev)

        for f,v in files:
            try:
                data = self.source.getfile(f, v)
            except IOError, inst:
                self.dest.delfile(f)
            else:
                e = self.source.getmode(f, v)
                self.dest.putfile(f, e, data)

        r = [self.map[v] for v in c.parents]
        f = [f for f,v in files]
        self.map[rev] = self.dest.putcommit(f, r, c)
        file(self.mapfile, "a").write("%s %s\n" % (rev, self.map[rev]))

    def convert(self):
        self.ui.status("scanning source...\n")
        heads = self.source.getheads()
        parents = self.walktree(heads)
        self.ui.status("sorting...\n")
        t = self.toposort(parents)
        num = len(t)
        c = None

        self.ui.status("converting...\n")
        for c in t:
            num -= 1
            desc = self.commitcache[c].desc
            if "\n" in desc:
                desc = desc.splitlines()[0]
            self.ui.status("%d %s\n" % (num, desc))
            self.copy(c)

        tags = self.source.gettags()
        ctags = {}
        for k in tags:
            v = tags[k]
            if v in self.map:
                ctags[k] = self.map[v]

        if c and ctags:
            nrev = self.dest.puttags(ctags)
            # write another hash correspondence to override the previous
            # one so we don't end up with extra tag heads
            if nrev:
                file(self.mapfile, "a").write("%s %s\n" % (c, nrev))

def _convert(ui, src, dest=None, mapfile=None, **opts):
    '''Convert a foreign SCM repository to a Mercurial one.

    Accepted source formats:
    - GIT
    - CVS

    Accepted destination formats:
    - Mercurial

    If destination isn't given, a new Mercurial repo named <src>-hg will
    be created. If <mapfile> isn't given, it will be put in a default
    location (<dest>/.hg/shamap by default)

    The <mapfile> is a simple text file that maps each source commit ID to
    the destination ID for that revision, like so:

    <source ID> <destination ID>

    If the file doesn't exist, it's automatically created.  It's updated
    on each commit copied, so convert-repo can be interrupted and can
    be run repeatedly to copy new commits.
    '''

    srcc = converter(ui, src)
    if not hasattr(srcc, "getcommit"):
        raise util.Abort("%s: can't read from this repo type\n" % src)

    if not dest:
        dest = src + "-hg"
        ui.status("assuming destination %s\n" % dest)

    # Try to be smart and initalize things when required
    if os.path.isdir(dest):
        if len(os.listdir(dest)) > 0:
            try:
                hg.repository(ui, dest)
                ui.status("destination %s is a Mercurial repository\n" % dest)
            except repo.RepoError:
                raise util.Abort(
"""destination directory %s is not empty.
Please specify an empty directory to be initialized or an already initialized
mercurial repository
""" % dest)
        else:
            ui.status("initializing destination %s repository\n" % dest)
            hg.repository(ui, dest, create=True)
    elif os.path.exists(dest):
        raise util.Abort("destination %s exists and is not a directory\n" % dest)
    else:
        ui.status("initializing destination %s repository\n" % dest)
        hg.repository(ui, dest, create=True)
  
    destc = converter(ui, dest)
    if not hasattr(destc, "putcommit"):
        raise util.Abort("%s: can't write to this repo type\n" % src)

    if not mapfile:
        try:
            mapfile = destc.mapfile()
        except:
            mapfile = os.path.join(destc, "map")

    c = convert(ui, srcc, destc, mapfile, opts)
    c.convert()

cmdtable = {
    "convert": (_convert,
                [('', 'datesort', None, 'try to sort changesets by date')],
                'hg convert [OPTIONS] <src> [dst [map]]'),
}
