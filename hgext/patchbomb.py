# Command for sending a collection of Mercurial changesets as a series
# of patch emails.
#
# The series is started off with a "[PATCH 0 of N]" introduction,
# which describes the series as a whole.
#
# Each patch email has a Subject line of "[PATCH M of N] ...", using
# the first line of the changeset description as the subject text.
# The message contains two or three body parts:
#
#   The remainder of the changeset description.
#
#   [Optional] If the diffstat program is installed, the result of
#   running diffstat on the patch.
#
#   The patch itself, as generated by "hg export".
#
# Each message refers to all of its predecessors using the In-Reply-To
# and References headers, so they will show up as a sequence in
# threaded mail and news readers, and in mail archives.
#
# For each changeset, you will be prompted with a diffstat summary and
# the changeset summary, so you can be sure you are sending the right
# changes.
#
# To enable this extension:
#
#   [extensions]
#   hgext.patchbomb =
#
# To configure other defaults, add a section like this to your hgrc
# file:
#
#   [email]
#   from = My Name <my@email>
#   to = recipient1, recipient2, ...
#   cc = cc1, cc2, ...
#   bcc = bcc1, bcc2, ...
#
# Then you can use the "hg email" command to mail a series of changesets
# as a patchbomb.
#
# To avoid sending patches prematurely, it is a good idea to first run
# the "email" command with the "-n" option (test only).  You will be
# prompted for an email recipient address, a subject an an introductory
# message describing the patches of your patchbomb.  Then when all is
# done, your pager will be fired up once for each patchbomb message, so
# you can verify everything is alright.
#
# The "-m" (mbox) option is also very useful.  Instead of previewing
# each patchbomb message in a pager or sending the messages directly,
# it will create a UNIX mailbox file with the patch emails.  This
# mailbox file can be previewed with any mail user agent which supports
# UNIX mbox files, i.e. with mutt:
#
#   % mutt -R -f mbox
#
# When you are previewing the patchbomb messages, you can use `formail'
# (a utility that is commonly installed as part of the procmail package),
# to send each message out:
#
#  % formail -s sendmail -bm -t < mbox
#
# That should be all.  Now your patchbomb is on its way out.

from mercurial.demandload import *
demandload(globals(), '''email.MIMEMultipart email.MIMEText email.Utils
                         mercurial:commands,hg,mail,ui
                         os errno popen2 socket sys tempfile time''')
from mercurial.i18n import gettext as _
from mercurial.node import *

try:
    # readline gives raw_input editing capabilities, but is not
    # present on windows
    import readline
except ImportError: pass

def diffstat(patch):
    fd, name = tempfile.mkstemp(prefix="hg-patchbomb-", suffix=".txt")
    try:
        p = popen2.Popen3('diffstat -p1 -w79 2>/dev/null > ' + name)
        try:
            for line in patch: print >> p.tochild, line
            p.tochild.close()
            if p.wait(): return
            fp = os.fdopen(fd, 'r')
            stat = []
            for line in fp: stat.append(line.lstrip())
            last = stat.pop()
            stat.insert(0, last)
            stat = ''.join(stat)
            if stat.startswith('0 files'): raise ValueError
            return stat
        except: raise
    finally:
        try: os.unlink(name)
        except: pass

def patchbomb(ui, repo, *revs, **opts):
    '''send changesets as a series of patch emails

    The series starts with a "[PATCH 0 of N]" introduction, which
    describes the series as a whole.

    Each patch email has a Subject line of "[PATCH M of N] ...", using
    the first line of the changeset description as the subject text.
    The message contains two or three body parts.  First, the rest of
    the changeset description.  Next, (optionally) if the diffstat
    program is installed, the result of running diffstat on the patch.
    Finally, the patch itself, as generated by "hg export".'''
    def prompt(prompt, default = None, rest = ': ', empty_ok = False):
        if default: prompt += ' [%s]' % default
        prompt += rest
        while True:
            r = raw_input(prompt)
            if r: return r
            if default is not None: return default
            if empty_ok: return r
            ui.warn(_('Please enter a valid value.\n'))

    def confirm(s):
        if not prompt(s, default = 'y', rest = '? ').lower().startswith('y'):
            raise ValueError

    def cdiffstat(summary, patch):
        s = diffstat(patch)
        if s:
            if summary:
                ui.write(summary, '\n')
                ui.write(s, '\n')
            confirm(_('Does the diffstat above look okay'))
        return s

    def makepatch(patch, idx, total):
        desc = []
        node = None
        body = ''
        for line in patch:
            if line.startswith('#'):
                if line.startswith('# Node ID'): node = line.split()[-1]
                continue
            if line.startswith('diff -r'): break
            desc.append(line)
        if not node: raise ValueError

        #body = ('\n'.join(desc[1:]).strip() or
        #        'Patch subject is complete summary.')
        #body += '\n\n\n'

        if opts['plain']:
            while patch and patch[0].startswith('# '): patch.pop(0)
            if patch: patch.pop(0)
            while patch and not patch[0].strip(): patch.pop(0)
        if opts['diffstat']:
            body += cdiffstat('\n'.join(desc), patch) + '\n\n'
        if opts['attach']:
            msg = email.MIMEMultipart.MIMEMultipart()
            if body: msg.attach(email.MIMEText.MIMEText(body, 'plain'))
            p = email.MIMEText.MIMEText('\n'.join(patch), 'x-patch')
            binnode = bin(node)
            # if node is mq patch, it will have patch file name as tag
            patchname = [t for t in repo.nodetags(binnode)
                         if t.endswith('.patch') or t.endswith('.diff')]
            if patchname:
                patchname = patchname[0]
            elif total > 1:
                patchname = commands.make_filename(repo, '%b-%n.patch',
                                                   binnode, idx, total)
            else:
                patchname = commands.make_filename(repo, '%b.patch', binnode)
            p['Content-Disposition'] = 'inline; filename=' + patchname
            msg.attach(p)
        else:
            body += '\n'.join(patch)
            msg = email.MIMEText.MIMEText(body)
        if total == 1:
            subj = '[PATCH] ' + desc[0].strip()
        else:
            subj = '[PATCH %d of %d] %s' % (idx, total, desc[0].strip())
        if subj.endswith('.'): subj = subj[:-1]
        msg['Subject'] = subj
        msg['X-Mercurial-Node'] = node
        return msg

    start_time = int(time.time())

    def genmsgid(id):
        return '<%s.%s@%s>' % (id[:20], start_time, socket.getfqdn())

    patches = []

    class exportee:
        def __init__(self, container):
            self.lines = []
            self.container = container
            self.name = 'email'

        def write(self, data):
            self.lines.append(data)

        def close(self):
            self.container.append(''.join(self.lines).split('\n'))
            self.lines = []

    commands.export(ui, repo, *revs, **{'output': exportee(patches),
                                        'switch_parent': False,
                                        'text': None})

    jumbo = []
    msgs = []

    ui.write(_('This patch series consists of %d patches.\n\n') % len(patches))

    for p, i in zip(patches, range(len(patches))):
        jumbo.extend(p)
        msgs.append(makepatch(p, i + 1, len(patches)))

    sender = (opts['from'] or ui.config('email', 'from') or
              ui.config('patchbomb', 'from') or
              prompt('From', ui.username()))

    def getaddrs(opt, prpt, default = None):
        addrs = opts[opt] or (ui.config('email', opt) or
                              ui.config('patchbomb', opt) or
                              prompt(prpt, default = default)).split(',')
        return [a.strip() for a in addrs if a.strip()]
    to = getaddrs('to', 'To')
    cc = getaddrs('cc', 'Cc', '')

    bcc = opts['bcc'] or (ui.config('email', 'bcc') or
                          ui.config('patchbomb', 'bcc') or '').split(',')
    bcc = [a.strip() for a in bcc if a.strip()]

    if len(patches) > 1:
        ui.write(_('\nWrite the introductory message for the patch series.\n\n'))

        subj = '[PATCH 0 of %d] %s' % (
            len(patches),
            opts['subject'] or
            prompt('Subject:', rest = ' [PATCH 0 of %d] ' % len(patches)))

        ui.write(_('Finish with ^D or a dot on a line by itself.\n\n'))

        body = []

        while True:
            try: l = raw_input()
            except EOFError: break
            if l == '.': break
            body.append(l)

        if opts['diffstat']:
            d = cdiffstat(_('Final summary:\n'), jumbo)
            if d: body.append('\n' + d)

        body = '\n'.join(body) + '\n'

        msg = email.MIMEText.MIMEText(body)
        msg['Subject'] = subj

        msgs.insert(0, msg)

    ui.write('\n')

    if not opts['test'] and not opts['mbox']:
        mailer = mail.connect(ui)
    parent = None

    # Calculate UTC offset
    if time.daylight: offset = time.altzone
    else: offset = time.timezone
    if offset <= 0: sign, offset = '+', -offset
    else: sign = '-'
    offset = '%s%02d%02d' % (sign, offset / 3600, (offset % 3600) / 60)

    sender_addr = email.Utils.parseaddr(sender)[1]
    for m in msgs:
        try:
            m['Message-Id'] = genmsgid(m['X-Mercurial-Node'])
        except TypeError:
            m['Message-Id'] = genmsgid('patchbomb')
        if parent:
            m['In-Reply-To'] = parent
        else:
            parent = m['Message-Id']
        m['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(start_time)) + ' ' + offset

        start_time += 1
        m['From'] = sender
        m['To'] = ', '.join(to)
        if cc: m['Cc']  = ', '.join(cc)
        if bcc: m['Bcc'] = ', '.join(bcc)
        if opts['test']:
            ui.status('Displaying ', m['Subject'], ' ...\n')
            fp = os.popen(os.getenv('PAGER', 'more'), 'w')
            try:
                fp.write(m.as_string(0))
                fp.write('\n')
            except IOError, inst:
                if inst.errno != errno.EPIPE:
                    raise
            fp.close()
        elif opts['mbox']:
            ui.status('Writing ', m['Subject'], ' ...\n')
            fp = open(opts['mbox'], m.has_key('In-Reply-To') and 'ab+' or 'wb+')
            date = time.asctime(time.localtime(start_time))
            fp.write('From %s %s\n' % (sender_addr, date))
            fp.write(m.as_string(0))
            fp.write('\n\n')
            fp.close()
        else:
            ui.status('Sending ', m['Subject'], ' ...\n')
            # Exim does not remove the Bcc field
            del m['Bcc']
            mailer.sendmail(sender, to + bcc + cc, m.as_string(0))

cmdtable = {
    'email':
    (patchbomb,
     [('a', 'attach', None, 'send patches as inline attachments'),
      ('', 'bcc', [], 'email addresses of blind copy recipients'),
      ('c', 'cc', [], 'email addresses of copy recipients'),
      ('d', 'diffstat', None, 'add diffstat output to messages'),
      ('f', 'from', '', 'email address of sender'),
      ('', 'plain', None, 'omit hg patch header'),
      ('n', 'test', None, 'print messages that would be sent'),
      ('m', 'mbox', '', 'write messages to mbox file instead of sending them'),
      ('s', 'subject', '', 'subject of introductory message'),
      ('t', 'to', [], 'email addresses of recipients')],
     "hg email [OPTION]... [REV]...")
    }
