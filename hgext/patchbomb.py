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
# It is best to run this script with the "-n" (test only) flag before
# firing it up "for real", in which case it will use your pager to
# display each of the messages that it would send.
#
# The "-m" (mbox) option will create an mbox file instead of sending
# the messages directly. This can be reviewed e.g. with "mutt -R -f mbox",
# and finally sent with "formail -s sendmail -bm -t < mbox".
#
# To configure a default mail host, add a section like this to your
# hgrc file:
#
# [smtp]
# host = my_mail_host
# port = 1025
# tls = yes # or omit if not needed
# username = user     # if SMTP authentication required
# password = password # if SMTP authentication required - PLAINTEXT
#
# To configure other defaults, add a section like this to your hgrc
# file:
#
# [patchbomb]
# from = My Name <my@email>
# to = recipient1, recipient2, ...
# cc = cc1, cc2, ...

from mercurial.demandload import *
demandload(globals(), '''email.MIMEMultipart email.MIMEText email.Utils
                         mercurial:commands,hg,ui
                         os errno popen2 smtplib socket sys tempfile time''')
from mercurial.i18n import gettext as _

try:
    # readline gives raw_input editing capabilities, but is not
    # present on windows
    import readline
except ImportError: pass

def diffstat(patch):
    fd, name = tempfile.mkstemp()
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

    sender = (opts['from'] or ui.config('patchbomb', 'from') or
              prompt('From', ui.username()))

    def getaddrs(opt, prpt, default = None):
        addrs = opts[opt] or (ui.config('patchbomb', opt) or
                              prompt(prpt, default = default)).split(',')
        return [a.strip() for a in addrs if a.strip()]
    to = getaddrs('to', 'To')
    cc = getaddrs('cc', 'Cc', '')

    if len(patches) > 1:
        ui.write(_('\nWrite the introductory message for the patch series.\n\n'))

        msg = email.MIMEMultipart.MIMEMultipart()
        msg['Subject'] = '[PATCH 0 of %d] %s' % (
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

        msg.attach(email.MIMEText.MIMEText('\n'.join(body) + '\n'))

        if opts['diffstat']:
            d = cdiffstat(_('Final summary:\n'), jumbo)
            if d: msg.attach(email.MIMEText.MIMEText(d))

        msgs.insert(0, msg)

    ui.write('\n')

    if not opts['test'] and not opts['mbox']:
        s = smtplib.SMTP()
        s.connect(host = ui.config('smtp', 'host', 'mail'),
                  port = int(ui.config('smtp', 'port', 25)))
        if ui.configbool('smtp', 'tls'):
            s.ehlo()
            s.starttls()
            s.ehlo()
        username = ui.config('smtp', 'username')
        password = ui.config('smtp', 'password')
        if username and password:
            s.login(username, password)
    parent = None
    tz = time.strftime('%z')
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
        m['Date'] = time.strftime('%a, %e %b %Y %T ', time.localtime(start_time)) + tz
        start_time += 1
        m['From'] = sender
        m['To'] = ', '.join(to)
        if cc: m['Cc'] = ', '.join(cc)
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
            s.sendmail(sender, to + cc, m.as_string(0))
    if not opts['test'] and not opts['mbox']:
        s.close()

cmdtable = {
    'email':
    (patchbomb,
     [('c', 'cc', [], 'email addresses of copy recipients'),
      ('d', 'diffstat', None, 'add diffstat output to messages'),
      ('f', 'from', '', 'email address of sender'),
      ('', 'plain', None, 'omit hg patch header'),
      ('n', 'test', None, 'print messages that would be sent'),
      ('m', 'mbox', '', 'write messages to mbox file instead of sending them'),
      ('s', 'subject', '', 'subject of introductory message'),
      ('t', 'to', [], 'email addresses of recipients')],
     "hg email [OPTION]... [REV]...")
    }
