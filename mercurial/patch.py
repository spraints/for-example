import cStringIO, email.Parser, os, re
import tempfile, zlib
import base85, mdiff, util, diffhelpers, copies, encoding
# helper functions

def copyfile(src, dst, basedir):
    abssrc, absdst = [util.canonpath(basedir, basedir, x) for x in [src, dst]]
    if os.path.lexists(absdst):
        raise util.Abort(_("cannot create %s: destination already exists") %
                         dst)

    dstdir = os.path.dirname(absdst)
    if dstdir and not os.path.isdir(dstdir):
        try:
            os.makedirs(dstdir)
        except IOError:
            raise util.Abort(
                _("cannot create %s: unable to create destination directory")
                % dst)

    util.copyfile(abssrc, absdst)
    if not hasattr(stream, 'next'):
    def __init__(self, fp, textmode=False):
        self.textmode = textmode
        self.eol = None
        l = self.fp.readline()
        if not self.eol:
            if l.endswith('\r\n'):
                self.eol = '\r\n'
            elif l.endswith('\n'):
                self.eol = '\n'
        if self.textmode and l.endswith('\r\n'):
            l = l[:-2] + '\n'
        return l
        while 1:
    def __init__(self, ui, fname, opener, missing=False, eolmode='strict'):
        self.fname = fname
        self.opener = opener
        self.missing = missing
        if not missing:
            try:
                self.lines = self.readlines(fname)
            except IOError:
                pass
        else:
            self.ui.warn(_("unable to find '%s' for patching\n") % self.fname)
    def readlines(self, fname):
        if os.path.islink(fname):
            return [os.readlink(fname)]
        fp = self.opener(fname, 'r')
        try:
            lr = linereader(fp, self.eolmode != 'strict')
            lines = list(lr)
            self.eol = lr.eol
            return lines
        finally:
            fp.close()

    def writelines(self, fname, lines):
        # Ensure supplied data ends in fname, being a regular file or
        # a symlink. cmdutil.updatedir will -too magically- take care
        # of setting it to the proper type afterwards.
        islink = os.path.islink(fname)
        if islink:
            fp = cStringIO.StringIO()
            fp = self.opener(fname, 'w')
        try:
            if self.eolmode == 'auto':
                eol = self.eol
            elif self.eolmode == 'crlf':
                eol = '\r\n'
            else:
                eol = '\n'
            if self.eolmode != 'strict' and eol and eol != '\n':
                for l in lines:
                    if l and l[-1] == '\n':
                        l = l[:-1] + eol
                    fp.write(l)
            else:
                fp.writelines(lines)
            if islink:
                self.opener.symlink(fp.getvalue(), fname)
        finally:
            fp.close()
    def unlink(self, fname):
        os.unlink(fname)
    def hashlines(self):
        self.hash = {}
        for x, s in enumerate(self.lines):
            self.hash.setdefault(s, []).append(x)



        fname = self.fname + ".rej"
        self.ui.warn(
            _("%d out of %d hunks FAILED -- saving rejects to file %s\n") %
            (len(self.rej), self.hunks, fname))

        def rejlines():
            base = os.path.basename(self.fname)
            yield "--- %s\n+++ %s\n" % (base, base)
            for x in self.rej:
                for l in x.hunk:
                    yield l
                    if l[-1] != '\n':
                        yield "\n\ No newline at end of file\n"

        self.writelines(fname, rejlines())
        if self.exists and h.createfile():
            self.ui.warn(_("file %s already exists\n") % self.fname)
            if h.rmfile():
                self.unlink(self.fname)
                self.dirty = 1
            if h.rmfile():
                self.unlink(self.fname)
                self.dirty = 1
        # ok, we couldn't match the hunk.  Lets look for offsets and fuzz it
        self.hashlines()
                        self.dirty = 1
    def __init__(self, desc, num, lr, context, create=False, remove=False):
        self.create = create
        self.remove = remove and not create
        nh = hunk(self.desc, self.number, None, None, False, False)
        nh.create = self.create
        nh.remove = self.remove
                # this can happen when the hunk does not add any lines
    def fix_newline(self):
        diffhelpers.fix_newline(self.hunk, self.a, self.b)
    def createfile(self):
        return self.starta == 0 and self.lena == 0 and self.create

    def rmfile(self):
        return self.startb == 0 and self.lenb == 0 and self.remove

class binhunk:
    def __init__(self, gitpatch):
        self.gitpatch = gitpatch

    def createfile(self):
        return self.gitpatch.op in ('ADD', 'RENAME', 'COPY')

    def rmfile(self):
        return self.gitpatch.op == 'DELETE'
    def extract(self, lr):
def selectfile(afile_orig, bfile_orig, hunk, strip):
    gooda = not nulla and os.path.lexists(afile)
        goodb = not nullb and os.path.lexists(bfile)
    createfunc = hunk.createfile
    missing = not goodb and not gooda and not createfunc()
    if missing and abasedir == bbasedir and afile.startswith(bfile):
        # this isn't very pretty
        hunk.create = True
        if createfunc():
            missing = False
        else:
            hunk.create = False
    return fname, missing
    gitlr = linereader(fp, lr.textmode)
def iterhunks(ui, fp, sourcefile=None):
    changed = {}
    current_hunk = None
    emitfile = False
    git = False
    # gitworkdone is True if a git operation (copy, rename, ...) was
    # performed already for the current file. Useful when the file
    # section may have no hunk.
    gitworkdone = False
        newfile = newgitfile = False
        if current_hunk:
            if x.startswith('\ '):
                current_hunk.fix_newline()
            yield 'hunk', current_hunk
            current_hunk = None
        if ((sourcefile or state == BFILE) and ((not context and x[0] == '@') or
            ((context is not False) and x.startswith('***************')))):
            if context is None and x.startswith('***************'):
                context = True
            gpatch = changed.get(bfile)
            create = afile == '/dev/null' or gpatch and gpatch.op == 'ADD'
            remove = bfile == '/dev/null' or gpatch and gpatch.op == 'DELETE'
            current_hunk = hunk(x, hunknum + 1, lr, context, create, remove)
                yield 'file', (afile, bfile, current_hunk)
        elif state == BFILE and x.startswith('GIT binary patch'):
            current_hunk = binhunk(changed[bfile])
            hunknum += 1
            if emitfile:
                emitfile = False
                yield 'file', ('a/' + afile, 'b/' + bfile, current_hunk)
            current_hunk.extract(lr)
            # check for git diff, scanning the whole patch file if needed
            gitworkdone = False
            if m:
                afile, bfile = m.group(1, 2)
                if not git:
                    git = True
                    gitpatches = scangitpatch(lr, x)
                    yield 'git', gitpatches
                    for gp in gitpatches:
                        changed[gp.path] = gp
                # else error?
                # copy/rename + modify should modify target, not source
                gp = changed.get(bfile)
                if gp and (gp.op in ('COPY', 'DELETE', 'RENAME', 'ADD')
                           or gp.mode):
                    afile = bfile
                    gitworkdone = True
                newgitfile = True
            gitworkdone = False

        if newgitfile or newfile:
    if current_hunk:
        if current_hunk.complete():
            yield 'hunk', current_hunk
        else:
            raise PatchError(_("malformed patch %s %s") % (afile,
                             current_hunk.desc))
def applydiff(ui, fp, changed, strip=1, sourcefile=None, eolmode='strict'):
    The dict 'changed' is filled in with all of the filenames changed
    by the patch. Returns 0 for a clean patch, -1 if any rejects were
    found and 1 if there was any fuzz.
    Callers probably want to call 'cmdutil.updatedir' after this to
    apply certain categories of changes not done by this function.
    """
    return _applydiff(
        ui, fp, patchfile, copyfile,
        changed, strip=strip, sourcefile=sourcefile, eolmode=eolmode)
def _applydiff(ui, fp, patcher, copyfn, changed, strip=1,
               sourcefile=None, eolmode='strict'):
    cwd = os.getcwd()
    opener = util.opener(cwd)
    def closefile():
        if not current_file:
            return 0
        if current_file.dirty:
            current_file.writelines(current_file.fname, current_file.lines)
        current_file.write_rej()
        return len(current_file.rej)

    for state, values in iterhunks(ui, fp, sourcefile):
            if ret >= 0:
                changed.setdefault(current_file.fname, None)
                if ret > 0:
                    err = 1
            rejects += closefile()
            afile, bfile, first_hunk = values
                if sourcefile:
                    current_file = patcher(ui, sourcefile, opener,
                                           eolmode=eolmode)
                else:
                    current_file, missing = selectfile(afile, bfile,
                                                       first_hunk, strip)
                    current_file = patcher(ui, current_file, opener,
                                           missing=missing, eolmode=eolmode)
            except PatchError, err:
                ui.warn(str(err) + '\n')
                gp.path = pathstrip(gp.path, strip - 1)[1]
                if gp.oldpath:
                    gp.oldpath = pathstrip(gp.oldpath, strip - 1)[1]
                # Binary patches really overwrite target files, copying them
                # will just make it fails with "target file exists"
                if gp.op in ('COPY', 'RENAME') and not gp.binary:
                    copyfn(gp.oldpath, gp.path, cwd)
                changed[gp.path] = gp
    rejects += closefile()
def externalpatch(patcher, patchname, ui, strip, cwd, files):

    for line in fp:
        line = line.rstrip()
        ui.note(line + '\n')
        if line.startswith('patching file '):
            pf = util.parse_patch_output(line)
            printed_file = False
            files.setdefault(pf, None)
        elif line.find('with fuzz') >= 0:
            fuzz = True
            if not printed_file:
                ui.warn(pf + '\n')
                printed_file = True
            ui.warn(line + '\n')
        elif line.find('saving rejects to file') >= 0:
            ui.warn(line + '\n')
        elif line.find('FAILED') >= 0:
            if not printed_file:
                ui.warn(pf + '\n')
                printed_file = True
            ui.warn(line + '\n')
                         util.explain_exit(code)[0])
def internalpatch(patchobj, ui, strip, cwd, files=None, eolmode='strict'):
    """use builtin patch to apply <patchobj> to the working directory.
    returns whether patch was applied with fuzz factor."""

        files = {}
    if cwd:
        curdir = os.getcwd()
        os.chdir(cwd)
        ret = applydiff(ui, fp, files, strip=strip, eolmode=eolmode)
        if cwd:
            os.chdir(curdir)
def patch(patchname, ui, strip=1, cwd=None, files=None, eolmode='strict'):
        files = {}
            return externalpatch(patcher, patchname, ui, strip, cwd, files)
        return internalpatch(patchname, ui, strip, cwd, files, eolmode)
        node1 = repo.dirstate.parents()[0]
            if filename:
                isbinary = adds == 0 and removes == 0
                yield (filename, adds, removes, isbinary)
            else:
                filename = line.split(None, 5)[-1]
    if filename:
        isbinary = adds == 0 and removes == 0
        yield (filename, adds, removes, isbinary)
    stats = list(diffstatdata(lines))

    maxtotal, maxname = 0, 0
    totaladds, totalremoves = 0, 0
    hasbinary = False

    sized = [(filename, adds, removes, isbinary, encoding.colwidth(filename))
             for filename, adds, removes, isbinary in stats]

    for filename, adds, removes, isbinary, namewidth in sized:
        totaladds += adds
        totalremoves += removes
        maxname = max(maxname, namewidth)
        maxtotal = max(maxtotal, adds + removes)
        if isbinary:
            hasbinary = True
    for filename, adds, removes, isbinary, namewidth in sized:
                      (filename, ' ' * (maxname - namewidth),
                       countwidth, count,
                       pluses, minuses))