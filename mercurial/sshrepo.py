# sshrepo.py - ssh repository proxy class for mercurial
#
# Copyright 2005 Matt Mackall <mpm@selenic.com>
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.

from node import *
from remoterepo import *
from i18n import gettext as _
from demandload import *
demandload(globals(), "hg os re stat util")

class sshrepository(remoterepository):
    def __init__(self, ui, path, create=0):
        self._url = path
        self.ui = ui

        m = re.match(r'ssh://(([^@]+)@)?([^:/]+)(:(\d+))?(/(.*))?', path)
        if not m:
            raise hg.RepoError(_("couldn't parse location %s") % path)

        self.user = m.group(2)
        self.host = m.group(3)
        self.port = m.group(5)
        self.path = m.group(7) or "."

        args = self.user and ("%s@%s" % (self.user, self.host)) or self.host
        args = self.port and ("%s -p %s") % (args, self.port) or args

        sshcmd = self.ui.config("ui", "ssh", "ssh")
        remotecmd = self.ui.config("ui", "remotecmd", "hg")

        if create:
            try:
                self.validate_repo(ui, sshcmd, args, remotecmd)
                return # the repo is good, nothing more to do
            except hg.RepoError:
                pass

            cmd = '%s %s "%s init %s"'
            cmd = cmd % (sshcmd, args, remotecmd, self.path)

            ui.note('running %s\n' % cmd)
            res = os.system(cmd)
            if res != 0:
                raise hg.RepoError(_("could not create remote repo"))

        self.validate_repo(ui, sshcmd, args, remotecmd)

    def url(self):
        return self._url

    def validate_repo(self, ui, sshcmd, args, remotecmd):
        cmd = '%s %s "%s -R %s serve --stdio"'
        cmd = cmd % (sshcmd, args, remotecmd, self.path)

        ui.note('running %s\n' % cmd)
        self.pipeo, self.pipei, self.pipee = os.popen3(cmd, 'b')

        # skip any noise generated by remote shell
        self.do_cmd("hello")
        r = self.do_cmd("between", pairs=("%s-%s" % ("0"*40, "0"*40)))
        lines = ["", "dummy"]
        max_noise = 500
        while lines[-1] and max_noise:
            l = r.readline()
            self.readerr()
            if lines[-1] == "1\n" and l == "\n":
                break
            if l:
                ui.debug(_("remote: "), l)
            lines.append(l)
            max_noise -= 1
        else:
            raise hg.RepoError(_("no response from remote hg"))

        self.capabilities = ()
        lines.reverse()
        for l in lines:
            if l.startswith("capabilities:"):
                self.capabilities = l[:-1].split(":")[1].split()
                break

    def readerr(self):
        while 1:
            size = util.fstat(self.pipee).st_size
            if size == 0: break
            l = self.pipee.readline()
            if not l: break
            self.ui.status(_("remote: "), l)

    def __del__(self):
        try:
            self.pipeo.close()
            self.pipei.close()
            # read the error descriptor until EOF
            for l in self.pipee:
                self.ui.status(_("remote: "), l)
            self.pipee.close()
        except:
            pass

    def do_cmd(self, cmd, **args):
        self.ui.debug(_("sending %s command\n") % cmd)
        self.pipeo.write("%s\n" % cmd)
        for k, v in args.items():
            self.pipeo.write("%s %d\n" % (k, len(v)))
            self.pipeo.write(v)
        self.pipeo.flush()

        return self.pipei

    def call(self, cmd, **args):
        r = self.do_cmd(cmd, **args)
        l = r.readline()
        self.readerr()
        try:
            l = int(l)
        except:
            raise hg.RepoError(_("unexpected response '%s'") % l)
        return r.read(l)

    def lock(self):
        self.call("lock")
        return remotelock(self)

    def unlock(self):
        self.call("unlock")

    def heads(self):
        d = self.call("heads")
        try:
            return map(bin, d[:-1].split(" "))
        except:
            raise hg.RepoError(_("unexpected response '%s'") % (d[:400] + "..."))

    def branches(self, nodes):
        n = " ".join(map(hex, nodes))
        d = self.call("branches", nodes=n)
        try:
            br = [ tuple(map(bin, b.split(" "))) for b in d.splitlines() ]
            return br
        except:
            raise hg.RepoError(_("unexpected response '%s'") % (d[:400] + "..."))

    def between(self, pairs):
        n = "\n".join(["-".join(map(hex, p)) for p in pairs])
        d = self.call("between", pairs=n)
        try:
            p = [ l and map(bin, l.split(" ")) or [] for l in d.splitlines() ]
            return p
        except:
            raise hg.RepoError(_("unexpected response '%s'") % (d[:400] + "..."))

    def changegroup(self, nodes, kind):
        n = " ".join(map(hex, nodes))
        return self.do_cmd("changegroup", roots=n)

    def unbundle(self, cg, heads, source):
        d = self.call("unbundle", heads=' '.join(map(hex, heads)))
        if d:
            raise hg.RepoError(_("push refused: %s") % d)

        while 1:
            d = cg.read(4096)
            if not d: break
            self.pipeo.write(str(len(d)) + '\n')
            self.pipeo.write(d)
            self.readerr()

        self.pipeo.write('0\n')
        self.pipeo.flush()

        self.readerr()
        d = self.pipei.readline()
        if d != '\n':
            return 1

        l = int(self.pipei.readline())
        r = self.pipei.read(l)
        if not r:
            return 1
        return int(r)

    def addchangegroup(self, cg, source, url):
        d = self.call("addchangegroup")
        if d:
            raise hg.RepoError(_("push refused: %s") % d)
        while 1:
            d = cg.read(4096)
            if not d: break
            self.pipeo.write(d)
            self.readerr()

        self.pipeo.flush()

        self.readerr()
        l = int(self.pipei.readline())
        r = self.pipei.read(l)
        if not r:
            return 1
        return int(r)

    def stream_out(self):
        return self.do_cmd('stream_out')

instance = sshrepository
