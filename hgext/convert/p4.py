#
# Perforce source for convert extension.
#
# Copyright 2009, Frank Kingswood <frank@kingswood-consulting.co.uk>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.
#

from mercurial import util
from mercurial.i18n import _

from common import commit, converter_source, checktool, NoRepo
import marshal
import re

def loaditer(f):
    "Yield the dictionary objects generated by p4"
    try:
        while True:
            d = marshal.load(f)
            if not d:
                break
            yield d
    except EOFError:
        pass

class p4_source(converter_source):
    def __init__(self, ui, path, rev=None):
        super(p4_source, self).__init__(ui, path, rev=rev)

        if "/" in path and not path.startswith('//'):
            raise NoRepo('%s does not look like a P4 repo' % path)

        checktool('p4', abort=False)

        self.p4changes = {}
        self.heads = {}
        self.changeset = {}
        self.files = {}
        self.tags = {}
        self.lastbranch = {}
        self.parent = {}
        self.encoding = "latin_1"
        self.depotname = {}           # mapping from local name to depot name
        self.modecache = {}
        self.re_type = re.compile("([a-z]+)?(text|binary|symlink|apple|resource|unicode|utf\d+)(\+\w+)?$")
        self.re_keywords = re.compile(r"\$(Id|Header|Date|DateTime|Change|File|Revision|Author):[^$\n]*\$")
        self.re_keywords_old = re.compile("\$(Id|Header):[^$\n]*\$")

        self._parse(ui, path)

    def _parse_view(self, path):
        "Read changes affecting the path"
        cmd = 'p4 -G changes -s submitted "%s"' % path
        stdout = util.popen(cmd, mode='rb')
        for d in loaditer(stdout):
            c = d.get("change", None)
            if c:
                self.p4changes[c] = True

    def _parse(self, ui, path):
        "Prepare list of P4 filenames and revisions to import"
        ui.status(_('reading p4 views\n'))

        # read client spec or view
        if "/" in path:
            self._parse_view(path)
            if path.startswith("//") and path.endswith("/..."):
                views = {path[:-3]:""}
            else:
                views = {"//": ""}
        else:
            cmd = 'p4 -G client -o "%s"' % path
            clientspec = marshal.load(util.popen(cmd, mode='rb'))

            views = {}
            for client in clientspec:
                if client.startswith("View"):
                    sview, cview = clientspec[client].split()
                    self._parse_view(sview)
                    if sview.endswith("...") and cview.endswith("..."):
                        sview = sview[:-3]
                        cview = cview[:-3]
                    cview = cview[2:]
                    cview = cview[cview.find("/") + 1:]
                    views[sview] = cview

        # list of changes that affect our source files
        self.p4changes = self.p4changes.keys()
        self.p4changes.sort(key=int)

        # list with depot pathnames, longest first
        vieworder = views.keys()
        vieworder.sort(key=len, reverse=True)

        # handle revision limiting
        startrev = self.ui.config('convert', 'p4.startrev', default=0)
        self.p4changes = [x for x in self.p4changes
                          if ((not startrev or int(x) >= int(startrev)) and
                              (not self.rev or int(x) <= int(self.rev)))]

        # now read the full changelists to get the list of file revisions
        ui.status(_('collecting p4 changelists\n'))
        lastid = None
        for change in self.p4changes:
            cmd = "p4 -G describe %s" % change
            stdout = util.popen(cmd, mode='rb')
            d = marshal.load(stdout)

            desc = self.recode(d["desc"])
            shortdesc = desc.split("\n", 1)[0]
            t = '%s %s' % (d["change"], repr(shortdesc)[1:-1])
            ui.status(util.ellipsis(t, 80) + '\n')

            if lastid:
                parents = [lastid]
            else:
                parents = []

            date = (int(d["time"]), 0)     # timezone not set
            c = commit(author=self.recode(d["user"]), date=util.datestr(date),
                        parents=parents, desc=desc, branch='', extra={"p4": change})

            files = []
            i = 0
            while ("depotFile%d" % i) in d and ("rev%d" % i) in d:
                oldname = d["depotFile%d" % i]
                filename = None
                for v in vieworder:
                    if oldname.startswith(v):
                        filename = views[v] + oldname[len(v):]
                        break
                if filename:
                    files.append((filename, d["rev%d" % i]))
                    self.depotname[filename] = oldname
                i += 1
            self.changeset[change] = c
            self.files[change] = files
            lastid = change

        if lastid:
            self.heads = [lastid]

    def getheads(self):
        return self.heads

    def getfile(self, name, rev):
        cmd = 'p4 -G print "%s#%s"' % (self.depotname[name], rev)
        stdout = util.popen(cmd, mode='rb')

        mode = None
        contents = ""
        keywords = None

        for d in loaditer(stdout):
            code = d["code"]
            data = d.get("data")

            if code == "error":
                raise IOError(d["generic"], data)

            elif code == "stat":
                p4type = self.re_type.match(d["type"])
                if p4type:
                    mode = ""
                    flags = (p4type.group(1) or "") + (p4type.group(3) or "")
                    if "x" in flags:
                        mode = "x"
                    if p4type.group(2) == "symlink":
                        mode = "l"
                    if "ko" in flags:
                        keywords = self.re_keywords_old
                    elif "k" in flags:
                        keywords = self.re_keywords

            elif code == "text" or code == "binary":
                contents += data

        if mode is None:
            raise IOError(0, "bad stat")

        self.modecache[(name, rev)] = mode

        if keywords:
            contents = keywords.sub("$\\1$", contents)
        if mode == "l" and contents.endswith("\n"):
            contents = contents[:-1]

        return contents

    def getmode(self, name, rev):
        return self.modecache[(name, rev)]

    def getchanges(self, rev):
        return self.files[rev], {}

    def getcommit(self, rev):
        return self.changeset[rev]

    def gettags(self):
        return self.tags

    def getchangedfiles(self, rev, i):
        return sorted([x[0] for x in self.files[rev]])
