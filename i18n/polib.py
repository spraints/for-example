# -*- coding: utf-8 -*-
# no-check-code
#
# License: MIT (see LICENSE file provided)
# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4:

"""
**polib** allows you to manipulate, create, modify gettext files (pot, po and
mo files).  You can load existing files, iterate through it's entries, add,
modify entries, comments or metadata, etc. or create new po files from scratch.

**polib** provides a simple and pythonic API via the :func:`~polib.pofile` and
:func:`~polib.mofile` convenience functions.
"""

__author__    = 'David Jean Louis <izimobil@gmail.com>'
__version__   = '0.6.4'
__all__       = ['pofile', 'POFile', 'POEntry', 'mofile', 'MOFile', 'MOEntry',
                 'detect_encoding', 'escape', 'unescape', 'detect_encoding',]

import array
import codecs
import os
import re
import struct
import sys
import textwrap
import types


# the default encoding to use when encoding cannot be detected
default_encoding = 'utf-8'

# _pofile_or_mofile {{{

def _pofile_or_mofile(f, type, **kwargs):
    """
    Internal function used by :func:`polib.pofile` and :func:`polib.mofile` to
    honor the DRY concept.
    """
    # get the file encoding
    enc = kwargs.get('encoding')
    if enc is None:
        enc = detect_encoding(f, type == 'mofile')

    # parse the file
    kls = type == 'pofile' and _POFileParser or _MOFileParser
    parser = kls(
        f,
        encoding=enc,
        check_for_duplicates=kwargs.get('check_for_duplicates', False)
    )
    instance = parser.parse()
    instance.wrapwidth = kwargs.get('wrapwidth', 78)
    return instance

# }}}
# function pofile() {{{

def pofile(pofile, **kwargs):
    """
    Convenience function that parses the po or pot file ``pofile`` and returns
    a :class:`~polib.POFile` instance.

    Arguments:

    ``pofile``
        string, full or relative path to the po/pot file or its content (data).

    ``wrapwidth``
        integer, the wrap width, only useful when the ``-w`` option was passed
        to xgettext (optional, default: ``78``).

    ``encoding``
        string, the encoding to use (e.g. "utf-8") (default: ``None``, the
        encoding will be auto-detected).

    ``check_for_duplicates``
        whether to check for duplicate entries when adding entries to the
        file (optional, default: ``False``).
    """
    return _pofile_or_mofile(pofile, 'pofile', **kwargs)

# }}}
# function mofile() {{{

def mofile(mofile, **kwargs):
    """
    Convenience function that parses the mo file ``mofile`` and returns a
    :class:`~polib.MOFile` instance.

    Arguments:

    ``mofile``
        string, full or relative path to the mo file or its content (data).

    ``wrapwidth``
        integer, the wrap width, only useful when the ``-w`` option was passed
        to xgettext to generate the po file that was used to format the mo file
        (optional, default: ``78``).

    ``encoding``
        string, the encoding to use (e.g. "utf-8") (default: ``None``, the
        encoding will be auto-detected).

    ``check_for_duplicates``
        whether to check for duplicate entries when adding entries to the
        file (optional, default: ``False``).
    """
    return _pofile_or_mofile(mofile, 'mofile', **kwargs)

# }}}
# function detect_encoding() {{{

def detect_encoding(file, binary_mode=False):
    """
    Try to detect the encoding used by the ``file``. The ``file`` argument can
    be a PO or MO file path or a string containing the contents of the file.
    If the encoding cannot be detected, the function will return the value of
    ``default_encoding``.

    Arguments:

    ``file``
        string, full or relative path to the po/mo file or its content.

    ``binary_mode``
        boolean, set this to True if ``file`` is a mo file.
    """
    rx = re.compile(r'"?Content-Type:.+? charset=([\w_\-:\.]+)')

    def charset_exists(charset):
        """Check whether ``charset`` is valid or not."""
        try:
            codecs.lookup(charset)
        except LookupError:
            return False
        return True

    if not os.path.exists(file):
        match = rx.search(file)
        if match:
            enc = match.group(1).strip()
            if charset_exists(enc):
                return enc
    else:
        if binary_mode:
            mode = 'rb'
        else:
            mode = 'r'
        f = open(file, mode)
        for l in f.readlines():
            match = rx.search(l)
            if match:
                f.close()
                enc = match.group(1).strip()
                if charset_exists(enc):
                    return enc
        f.close()
    return default_encoding

# }}}
# function escape() {{{

def escape(st):
    """
    Escapes the characters ``\\\\``, ``\\t``, ``\\n``, ``\\r`` and ``"`` in
    the given string ``st`` and returns it.
    """
    return st.replace('\\', r'\\')\
             .replace('\t', r'\t')\
             .replace('\r', r'\r')\
             .replace('\n', r'\n')\
             .replace('\"', r'\"')

# }}}
# function unescape() {{{

def unescape(st):
    """
    Unescapes the characters ``\\\\``, ``\\t``, ``\\n``, ``\\r`` and ``"`` in
    the given string ``st`` and returns it.
    """
    def unescape_repl(m):
        m = m.group(1)
        if m == 'n':
            return '\n'
        if m == 't':
            return '\t'
        if m == 'r':
            return '\r'
        if m == '\\':
            return '\\'
        return m # handles escaped double quote
    return re.sub(r'\\(\\|n|t|r|")', unescape_repl, st)

# }}}
# class _BaseFile {{{

class _BaseFile(list):
    """
    Common base class for the :class:`~polib.POFile` and :class:`~polib.MOFile`
    classes. This class should **not** be instanciated directly.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor, accepts the following keyword arguments:

        ``pofile``
            string, the path to the po or mo file, or its content as a string.

        ``wrapwidth``
            integer, the wrap width, only useful when the ``-w`` option was
            passed to xgettext (optional, default: ``78``).

        ``encoding``
            string, the encoding to use, defaults to ``default_encoding``
            global variable (optional).

        ``check_for_duplicates``
            whether to check for duplicate entries when adding entries to the
            file, (optional, default: ``False``).
        """
        list.__init__(self)
        # the opened file handle
        pofile = kwargs.get('pofile', None)
        if pofile and os.path.exists(pofile):
            self.fpath = pofile
        else:
            self.fpath = kwargs.get('fpath')
        # the width at which lines should be wrapped
        self.wrapwidth = kwargs.get('wrapwidth', 78)
        # the file encoding
        self.encoding = kwargs.get('encoding', default_encoding)
        # whether to check for duplicate entries or not
        self.check_for_duplicates = kwargs.get('check_for_duplicates', False)
        # header
        self.header = ''
        # both po and mo files have metadata
        self.metadata = {}
        self.metadata_is_fuzzy = 0

    def __unicode__(self):
        """
        Returns the unicode representation of the file.
        """
        ret = []
        entries = [self.metadata_as_entry()] + \
                  [e for e in self if not e.obsolete]
        for entry in entries:
            ret.append(entry.__unicode__(self.wrapwidth))
        for entry in self.obsolete_entries():
            ret.append(entry.__unicode__(self.wrapwidth))
        ret = '\n'.join(ret)

        if type(ret) != types.UnicodeType:
            return unicode(ret, self.encoding)
        return ret

    def __str__(self):
        """
        Returns the string representation of the file.
        """
        return unicode(self).encode(self.encoding)

    def __contains__(self, entry):
        """
        Overriden ``list`` method to implement the membership test (in and
        not in).
        The method considers that an entry is in the file if it finds an entry
        that has the same msgid (the test is **case sensitive**).

        Argument:

        ``entry``
            an instance of :class:`~polib._BaseEntry`.
        """
        return self.find(entry.msgid, by='msgid') is not None
    
    def __eq__(self, other):
        return unicode(self) == unicode(other)

    def append(self, entry):
        """
        Overriden method to check for duplicates entries, if a user tries to
        add an entry that is already in the file, the method will raise a
        ``ValueError`` exception.

        Argument:

        ``entry``
            an instance of :class:`~polib._BaseEntry`.
        """
        if self.check_for_duplicates and entry in self:
            raise ValueError('Entry "%s" already exists' % entry.msgid)
        super(_BaseFile, self).append(entry)

    def insert(self, index, entry):
        """
        Overriden method to check for duplicates entries, if a user tries to
        add an entry that is already in the file, the method will raise a
        ``ValueError`` exception.

        Arguments:

        ``index``
            index at which the entry should be inserted.

        ``entry``
            an instance of :class:`~polib._BaseEntry`.
        """
        if self.check_for_duplicates and entry in self:
            raise ValueError('Entry "%s" already exists' % entry.msgid)
        super(_BaseFile, self).insert(index, entry)

    def metadata_as_entry(self):
        """
        Returns the file metadata as a :class:`~polib.POFile` instance.
        """
        e = POEntry(msgid='')
        mdata = self.ordered_metadata()
        if mdata:
            strs = []
            for name, value in mdata:
                # Strip whitespace off each line in a multi-line entry
                strs.append('%s: %s' % (name, value))
            e.msgstr = '\n'.join(strs) + '\n'
        if self.metadata_is_fuzzy:
            e.flags.append('fuzzy')
        return e

    def save(self, fpath=None, repr_method='__str__'):
        """
        Saves the po file to ``fpath``.
        If it is an existing file and no ``fpath`` is provided, then the
        existing file is rewritten with the modified data.

        Keyword arguments:

        ``fpath``
            string, full or relative path to the file.

        ``repr_method``
            string, the method to use for output.
        """
        if self.fpath is None and fpath is None:
            raise IOError('You must provide a file path to save() method')
        contents = getattr(self, repr_method)()
        if fpath is None:
            fpath = self.fpath
        if repr_method == 'to_binary':
            fhandle = open(fpath, 'wb')
        else:
            fhandle = codecs.open(fpath, 'w', self.encoding)
            if type(contents) != types.UnicodeType:
                contents = contents.decode(self.encoding)
        fhandle.write(contents)
        fhandle.close()
        # set the file path if not set
        if self.fpath is None and fpath:
            self.fpath = fpath

    def find(self, st, by='msgid', include_obsolete_entries=False,
             msgctxt=False):
        """
        Find the entry which msgid (or property identified by the ``by``
        argument) matches the string ``st``.

        Keyword arguments:

        ``st``
            string, the string to search for.

        ``by``
            string, the property to use for comparison (default: ``msgid``).

        ``include_obsolete_entries``
            boolean, whether to also search in entries that are obsolete.

        ``msgctxt``
            string, allows to specify a specific message context for the
            search.
        """
        if include_obsolete_entries:
            entries = self[:]
        else:
            entries = [e for e in self if not e.obsolete]
        for e in entries:
            if getattr(e, by) == st:
                if msgctxt and e.msgctxt != msgctxt:
                    continue
                return e
        return None

    def ordered_metadata(self):
        """
        Convenience method that returns an ordered version of the metadata
        dictionnary. The return value is list of tuples (metadata name,
        metadata_value).
        """
        # copy the dict first
        metadata = self.metadata.copy()
        data_order = [
            'Project-Id-Version',
            'Report-Msgid-Bugs-To',
            'POT-Creation-Date',
            'PO-Revision-Date',
            'Last-Translator',
            'Language-Team',
            'MIME-Version',
            'Content-Type',
            'Content-Transfer-Encoding'
        ]
        ordered_data = []
        for data in data_order:
            try:
                value = metadata.pop(data)
                ordered_data.append((data, value))
            except KeyError:
                pass
        # the rest of the metadata will be alphabetically ordered since there
        # are no specs for this AFAIK
        keys = metadata.keys()
        keys.sort()
        for data in keys:
            value = metadata[data]
            ordered_data.append((data, value))
        return ordered_data

    def to_binary(self):
        """
        Return the binary representation of the file.
        """
        offsets = []
        entries = self.translated_entries()
        # the keys are sorted in the .mo file
        def cmp(_self, other):
            # msgfmt compares entries with msgctxt if it exists
            self_msgid = _self.msgctxt and _self.msgctxt or _self.msgid
            other_msgid = other.msgctxt and other.msgctxt or other.msgid
            if self_msgid > other_msgid:
                return 1
            elif self_msgid < other_msgid:
                return -1
            else:
                return 0
        # add metadata entry
        entries.sort(cmp)
        mentry = self.metadata_as_entry()
        #mentry.msgstr = mentry.msgstr.replace('\\n', '').lstrip()
        entries = [mentry] + entries
        entries_len = len(entries)
        ids, strs = '', ''
        for e in entries:
            # For each string, we need size and file offset.  Each string is
            # NUL terminated; the NUL does not count into the size.
            msgid = ''
            if e.msgctxt:
                # Contexts are stored by storing the concatenation of the
                # context, a <EOT> byte, and the original string
                msgid = self._encode(e.msgctxt + '\4')
            if e.msgid_plural:
                indexes = e.msgstr_plural.keys()
                indexes.sort()
                msgstr = []
                for index in indexes:
                    msgstr.append(e.msgstr_plural[index])
                msgid += self._encode(e.msgid + '\0' + e.msgid_plural)
                msgstr = self._encode('\0'.join(msgstr))
            else:
                msgid += self._encode(e.msgid)
                msgstr = self._encode(e.msgstr)
            offsets.append((len(ids), len(msgid), len(strs), len(msgstr)))
            ids  += msgid  + '\0'
            strs += msgstr + '\0'

        # The header is 7 32-bit unsigned integers.
        keystart = 7*4+16*entries_len
        # and the values start after the keys
        valuestart = keystart + len(ids)
        koffsets = []
        voffsets = []
        # The string table first has the list of keys, then the list of values.
        # Each entry has first the size of the string, then the file offset.
        for o1, l1, o2, l2 in offsets:
            koffsets += [l1, o1+keystart]
            voffsets += [l2, o2+valuestart]
        offsets = koffsets + voffsets
        # check endianness for magic number
        if struct.pack('@h', 1) == struct.pack('<h', 1):
            magic_number = MOFile.LITTLE_ENDIAN
        else:
            magic_number = MOFile.BIG_ENDIAN

        output = struct.pack(
            "Iiiiiii",
            magic_number,      # Magic number
            0,                 # Version
            entries_len,       # # of entries
            7*4,               # start of key index
            7*4+entries_len*8, # start of value index
            0, keystart        # size and offset of hash table
                               # Important: we don't use hash tables
        )              
        output += array.array("i", offsets).tostring()
        output += ids
        output += strs
        return output

    def _encode(self, mixed):
        """
        Encodes the given ``mixed`` argument with the file encoding if and
        only if it's an unicode string and returns the encoded string.
        """
        if type(mixed) == types.UnicodeType:
            return mixed.encode(self.encoding)
        return mixed

# }}}
# class POFile {{{

class POFile(_BaseFile):
    """
    Po (or Pot) file reader/writer.
    This class inherits the :class:`~polib._BaseFile` class and, by extension,
    the python ``list`` type.
    """

    def __unicode__(self):
        """
        Returns the unicode representation of the po file.
        """
        ret, headers = '', self.header.split('\n')
        for header in headers:
            if header[:1] in [',', ':']:
                ret += '#%s\n' % header
            else:
                ret += '# %s\n' % header

        if type(ret) != types.UnicodeType:
            ret = unicode(ret, self.encoding)

        return ret + _BaseFile.__unicode__(self)

    def save_as_mofile(self, fpath):
        """
        Saves the binary representation of the file to given ``fpath``.

        Keyword argument:

        ``fpath``
            string, full or relative path to the mo file.
        """
        _BaseFile.save(self, fpath, 'to_binary')

    def percent_translated(self):
        """
        Convenience method that returns the percentage of translated
        messages.
        """
        total = len([e for e in self if not e.obsolete])
        if total == 0:
            return 100
        translated = len(self.translated_entries())
        return int((100.00 / float(total)) * translated)

    def translated_entries(self):
        """
        Convenience method that returns the list of translated entries.
        """
        return [e for e in self if e.translated()]

    def untranslated_entries(self):
        """
        Convenience method that returns the list of untranslated entries.
        """
        return [e for e in self if not e.translated() and not e.obsolete \
                and not 'fuzzy' in e.flags]

    def fuzzy_entries(self):
        """
        Convenience method that returns the list of fuzzy entries.
        """
        return [e for e in self if 'fuzzy' in e.flags]

    def obsolete_entries(self):
        """
        Convenience method that returns the list of obsolete entries.
        """
        return [e for e in self if e.obsolete]

    def merge(self, refpot):
        """
        Convenience method that merges the current pofile with the pot file
        provided. It behaves exactly as the gettext msgmerge utility:

        * comments of this file will be preserved, but extracted comments and
          occurrences will be discarded;
        * any translations or comments in the file will be discarded, however,
          dot comments and file positions will be preserved;
        * the fuzzy flags are preserved.

        Keyword argument:

        ``refpot``
            object POFile, the reference catalog.
        """
        for entry in refpot:
            e = self.find(entry.msgid, include_obsolete_entries=True)
            if e is None:
                e = POEntry()
                self.append(e)
            e.merge(entry)
        # ok, now we must "obsolete" entries that are not in the refpot anymore
        for entry in self:
            if refpot.find(entry.msgid) is None:
                entry.obsolete = True

# }}}
# class MOFile {{{

class MOFile(_BaseFile):
    """
    Mo file reader/writer.
    This class inherits the :class:`~polib._BaseFile` class and, by
    extension, the python ``list`` type.
    """
    BIG_ENDIAN    = 0xde120495
    LITTLE_ENDIAN = 0x950412de

    def __init__(self, *args, **kwargs):
        """
        Constructor, accepts all keywords arguments accepted by 
        :class:`~polib._BaseFile` class.
        """
        _BaseFile.__init__(self, *args, **kwargs)
        self.magic_number = None
        self.version = 0

    def save_as_pofile(self, fpath):
        """
        Saves the mofile as a pofile to ``fpath``.

        Keyword argument:

        ``fpath``
            string, full or relative path to the file.
        """
        _BaseFile.save(self, fpath)

    def save(self, fpath=None):
        """
        Saves the mofile to ``fpath``.

        Keyword argument:

        ``fpath``
            string, full or relative path to the file.
        """
        _BaseFile.save(self, fpath, 'to_binary')

    def percent_translated(self):
        """
        Convenience method to keep the same interface with POFile instances.
        """
        return 100

    def translated_entries(self):
        """
        Convenience method to keep the same interface with POFile instances.
        """
        return self

    def untranslated_entries(self):
        """
        Convenience method to keep the same interface with POFile instances.
        """
        return []

    def fuzzy_entries(self):
        """
        Convenience method to keep the same interface with POFile instances.
        """
        return []

    def obsolete_entries(self):
        """
        Convenience method to keep the same interface with POFile instances.
        """
        return []

# }}}
# class _BaseEntry {{{

class _BaseEntry(object):
    """
    Base class for :class:`~polib.POEntry` and :class:`~polib.MOEntry` classes.
    This class should **not** be instanciated directly.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor, accepts the following keyword arguments:

        ``msgid``
            string, the entry msgid.

        ``msgstr``
            string, the entry msgstr.

        ``msgid_plural``
            string, the entry msgid_plural.

        ``msgstr_plural``
            list, the entry msgstr_plural lines.

        ``msgctxt``
            string, the entry context (msgctxt).

        ``obsolete``
            bool, whether the entry is "obsolete" or not.

        ``encoding``
            string, the encoding to use, defaults to ``default_encoding``
            global variable (optional).
        """
        self.msgid = kwargs.get('msgid', '')
        self.msgstr = kwargs.get('msgstr', '')
        self.msgid_plural = kwargs.get('msgid_plural', '')
        self.msgstr_plural = kwargs.get('msgstr_plural', {})
        self.msgctxt = kwargs.get('msgctxt', None)
        self.obsolete = kwargs.get('obsolete', False)
        self.encoding = kwargs.get('encoding', default_encoding)

    def __unicode__(self, wrapwidth=78):
        """
        Returns the unicode representation of the entry.
        """
        if self.obsolete:
            delflag = '#~ '
        else:
            delflag = ''
        ret = []
        # write the msgctxt if any
        if self.msgctxt is not None:
            ret += self._str_field("msgctxt", delflag, "", self.msgctxt, wrapwidth)
        # write the msgid
        ret += self._str_field("msgid", delflag, "", self.msgid, wrapwidth)
        # write the msgid_plural if any
        if self.msgid_plural:
            ret += self._str_field("msgid_plural", delflag, "", self.msgid_plural, wrapwidth)
        if self.msgstr_plural:
            # write the msgstr_plural if any
            msgstrs = self.msgstr_plural
            keys = list(msgstrs)
            keys.sort()
            for index in keys:
                msgstr = msgstrs[index]
                plural_index = '[%s]' % index
                ret += self._str_field("msgstr", delflag, plural_index, msgstr, wrapwidth)
        else:
            # otherwise write the msgstr
            ret += self._str_field("msgstr", delflag, "", self.msgstr, wrapwidth)
        ret.append('')
        ret = '\n'.join(ret)

        if type(ret) != types.UnicodeType:
            return unicode(ret, self.encoding)
        return ret

    def __str__(self):
        """
        Returns the string representation of the entry.
        """
        return unicode(self).encode(self.encoding)
    
    def __eq__(self, other):
        return unicode(self) == unicode(other)

    def _str_field(self, fieldname, delflag, plural_index, field, wrapwidth=78):
        lines = field.splitlines(True)
        if len(lines) > 1:
            lines = [''] + lines # start with initial empty line
        else:
            escaped_field = escape(field)
            specialchars_count = 0
            for c in ['\\', '\n', '\r', '\t', '"']:
                specialchars_count += field.count(c)
            # comparison must take into account fieldname length + one space 
            # + 2 quotes (eg. msgid "<string>")
            flength = len(fieldname) + 3
            if plural_index:
                flength += len(plural_index)
            real_wrapwidth = wrapwidth - flength + specialchars_count
            if wrapwidth > 0 and len(field) > real_wrapwidth:
                # Wrap the line but take field name into account
                lines = [''] + [unescape(item) for item in wrap(
                    escaped_field,
                    wrapwidth - 2, # 2 for quotes ""
                    drop_whitespace=False,
                    break_long_words=False
                )]
            else:
                lines = [field]
        if fieldname.startswith('previous_'):
            # quick and dirty trick to get the real field name
            fieldname = fieldname[9:]

        ret = ['%s%s%s "%s"' % (delflag, fieldname, plural_index,
                                escape(lines.pop(0)))]
        for mstr in lines:
            ret.append('%s"%s"' % (delflag, escape(mstr)))
        return ret

# }}}
# class POEntry {{{

class POEntry(_BaseEntry):
    """
    Represents a po file entry.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor, accepts the following keyword arguments:

        ``comment``
            string, the entry comment.

        ``tcomment``
            string, the entry translator comment.

        ``occurrences``
            list, the entry occurrences.

        ``flags``
            list, the entry flags.

        ``previous_msgctxt``
            string, the entry previous context.

        ``previous_msgid``
            string, the entry previous msgid.

        ``previous_msgid_plural``
            string, the entry previous msgid_plural.
        """
        _BaseEntry.__init__(self, *args, **kwargs)
        self.comment = kwargs.get('comment', '')
        self.tcomment = kwargs.get('tcomment', '')
        self.occurrences = kwargs.get('occurrences', [])
        self.flags = kwargs.get('flags', [])
        self.previous_msgctxt = kwargs.get('previous_msgctxt', None)
        self.previous_msgid = kwargs.get('previous_msgid', None)
        self.previous_msgid_plural = kwargs.get('previous_msgid_plural', None)

    def __unicode__(self, wrapwidth=78):
        """
        Returns the unicode representation of the entry.
        """
        if self.obsolete:
            return _BaseEntry.__unicode__(self, wrapwidth)

        ret = []
        # comments first, if any (with text wrapping as xgettext does)
        comments = [('comment', '#. '), ('tcomment', '# ')]
        for c in comments:
            val = getattr(self, c[0])
            if val:
                for comment in val.split('\n'):
                    if wrapwidth > 0 and len(comment) + len(c[1]) > wrapwidth:
                        ret += wrap(
                            comment,
                            wrapwidth,
                            initial_indent=c[1],
                            subsequent_indent=c[1],
                            break_long_words=False
                        )
                    else:
                        ret.append('%s%s' % (c[1], comment))

        # occurrences (with text wrapping as xgettext does)
        if self.occurrences:
            filelist = []
            for fpath, lineno in self.occurrences:
                if lineno:
                    filelist.append('%s:%s' % (fpath, lineno))
                else:
                    filelist.append(fpath)
            filestr = ' '.join(filelist)
            if wrapwidth > 0 and len(filestr) + 3 > wrapwidth:
                # textwrap split words that contain hyphen, this is not 
                # what we want for filenames, so the dirty hack is to 
                # temporally replace hyphens with a char that a file cannot 
                # contain, like "*"
                ret += [l.replace('*', '-') for l in wrap(
                    filestr.replace('-', '*'),
                    wrapwidth,
                    initial_indent='#: ',
                    subsequent_indent='#: ',
                    break_long_words=False
                )]
            else:
                ret.append('#: ' + filestr)

        # flags (TODO: wrapping ?)
        if self.flags:
            ret.append('#, %s' % ', '.join(self.flags))

        # previous context and previous msgid/msgid_plural
        fields = ['previous_msgctxt', 'previous_msgid', 'previous_msgid_plural']
        for f in fields:
            val = getattr(self, f)
            if val:
                ret += self._str_field(f, "#| ", "", val, wrapwidth)

        ret.append(_BaseEntry.__unicode__(self, wrapwidth))
        ret = '\n'.join(ret)

        if type(ret) != types.UnicodeType:
            return unicode(ret, self.encoding)
        return ret

    def __cmp__(self, other):
        """
        Called by comparison operations if rich comparison is not defined.
        """
        def compare_occurrences(a, b):
            """
            Compare an entry occurrence with another one.
            """
            if a[0] != b[0]:
                return a[0] < b[0]
            if a[1] != b[1]:
                return a[1] < b[1]
            return 0

        # First: Obsolete test
        if self.obsolete != other.obsolete:
            if self.obsolete:
                return -1
            else:
                return 1
        # Work on a copy to protect original
        occ1 = self.occurrences[:]
        occ2 = other.occurrences[:]
        # Sorting using compare method
        occ1.sort(compare_occurrences)
        occ2.sort(compare_occurrences)
        # Comparing sorted occurrences
        pos = 0
        for entry1 in occ1:
            try:
                entry2 = occ2[pos]
            except IndexError:
                return 1
            pos = pos + 1
            if entry1[0] != entry2[0]:
                if entry1[0] > entry2[0]:
                    return 1
                else:
                    return -1
            if entry1[1] != entry2[1]:
                if entry1[1] > entry2[1]:
                    return 1
                else:
                    return -1
        # Finally: Compare message ID
        if self.msgid > other.msgid: return 1
        else: return -1

    def translated(self):
        """
        Returns ``True`` if the entry has been translated or ``False``
        otherwise.
        """
        if self.obsolete or 'fuzzy' in self.flags:
            return False
        if self.msgstr != '':
            return True
        if self.msgstr_plural:
            for pos in self.msgstr_plural:
                if self.msgstr_plural[pos] == '':
                    return False
            return True
        return False

    def merge(self, other):
        """
        Merge the current entry with the given pot entry.
        """
        self.msgid = other.msgid
        self.msgctxt = other.msgctxt
        self.occurrences = other.occurrences
        self.comment = other.comment
        fuzzy = 'fuzzy' in self.flags
        self.flags = other.flags[:]  # clone flags
        if fuzzy:
            self.flags.append('fuzzy')
        self.msgid_plural = other.msgid_plural
        self.obsolete = other.obsolete
        self.previous_msgctxt = other.previous_msgctxt
        self.previous_msgid = other.previous_msgid
        self.previous_msgid_plural = other.previous_msgid_plural
        if other.msgstr_plural:
            for pos in other.msgstr_plural:
                try:
                    # keep existing translation at pos if any
                    self.msgstr_plural[pos]
                except KeyError:
                    self.msgstr_plural[pos] = ''

# }}}
# class MOEntry {{{

class MOEntry(_BaseEntry):
    """
    Represents a mo file entry.
    """
    pass

# }}}
# class _POFileParser {{{

class _POFileParser(object):
    """
    A finite state machine to parse efficiently and correctly po
    file format.
    """

    def __init__(self, pofile, *args, **kwargs):
        """
        Constructor.

        Keyword arguments:

        ``pofile``
            string, path to the po file or its content

        ``encoding``
            string, the encoding to use, defaults to ``default_encoding``
            global variable (optional).

        ``check_for_duplicates``
            whether to check for duplicate entries when adding entries to the
            file (optional, default: ``False``).
        """
        enc = kwargs.get('encoding', default_encoding)
        if os.path.exists(pofile):
            try:
                self.fhandle = codecs.open(pofile, 'rU', enc)
            except LookupError:
                enc = default_encoding
                self.fhandle = codecs.open(pofile, 'rU', enc)
        else:
            self.fhandle = pofile.splitlines()

        self.instance = POFile(
            pofile=pofile,
            encoding=enc,
            check_for_duplicates=kwargs.get('check_for_duplicates', False)
        )
        self.transitions = {}
        self.current_entry = POEntry()
        self.current_state = 'ST'
        self.current_token = None
        # two memo flags used in handlers
        self.msgstr_index = 0
        self.entry_obsolete = 0
        # Configure the state machine, by adding transitions.
        # Signification of symbols:
        #     * ST: Beginning of the file (start)
        #     * HE: Header
        #     * TC: a translation comment
        #     * GC: a generated comment
        #     * OC: a file/line occurence
        #     * FL: a flags line
        #     * CT: a message context
        #     * PC: a previous msgctxt
        #     * PM: a previous msgid
        #     * PP: a previous msgid_plural
        #     * MI: a msgid
        #     * MP: a msgid plural
        #     * MS: a msgstr
        #     * MX: a msgstr plural
        #     * MC: a msgid or msgstr continuation line
        all = ['ST', 'HE', 'GC', 'OC', 'FL', 'CT', 'PC', 'PM', 'PP', 'TC',
               'MS', 'MP', 'MX', 'MI']

        self.add('TC', ['ST', 'HE'],                                     'HE')
        self.add('TC', ['GC', 'OC', 'FL', 'TC', 'PC', 'PM', 'PP', 'MS',
                        'MP', 'MX', 'MI'],                               'TC')
        self.add('GC', all,                                              'GC')
        self.add('OC', all,                                              'OC')
        self.add('FL', all,                                              'FL')
        self.add('PC', all,                                              'PC')
        self.add('PM', all,                                              'PM')
        self.add('PP', all,                                              'PP')
        self.add('CT', ['ST', 'HE', 'GC', 'OC', 'FL', 'TC', 'PC', 'PM',
                        'PP', 'MS', 'MX'],                               'CT')
        self.add('MI', ['ST', 'HE', 'GC', 'OC', 'FL', 'CT', 'TC', 'PC', 
                 'PM', 'PP', 'MS', 'MX'],                                'MI')
        self.add('MP', ['TC', 'GC', 'PC', 'PM', 'PP', 'MI'],             'MP')
        self.add('MS', ['MI', 'MP', 'TC'],                               'MS')
        self.add('MX', ['MI', 'MX', 'MP', 'TC'],                         'MX')
        self.add('MC', ['CT', 'MI', 'MP', 'MS', 'MX', 'PM', 'PP', 'PC'], 'MC')

    def parse(self):
        """
        Run the state machine, parse the file line by line and call process()
        with the current matched symbol.
        """
        i = 0

        keywords = {
            'msgctxt': 'CT',
            'msgid': 'MI',
            'msgstr': 'MS',
            'msgid_plural': 'MP',
        }
        prev_keywords = {
            'msgid_plural': 'PP',
            'msgid': 'PM',
            'msgctxt': 'PC',
        }

        for line in self.fhandle:
            i += 1
            line = line.strip()
            if line == '':
                continue

            tokens = line.split(None, 2)
            nb_tokens = len(tokens)

            if tokens[0] == '#~' and nb_tokens > 1:
                line = line[3:].strip()
                tokens = tokens[1:]
                nb_tokens -= 1
                self.entry_obsolete = 1
            else:
                self.entry_obsolete = 0

            # Take care of keywords like
            # msgid, msgid_plural, msgctxt & msgstr.
            if tokens[0] in keywords and nb_tokens > 1:
                line = line[len(tokens[0]):].lstrip()
                self.current_token = line
                self.process(keywords[tokens[0]], i)
                continue

            self.current_token = line

            if tokens[0] == '#:' and nb_tokens > 1:
                # we are on a occurrences line
                self.process('OC', i)

            elif line[:1] == '"':
                # we are on a continuation line
                self.process('MC', i)

            elif line[:7] == 'msgstr[':
                # we are on a msgstr plural
                self.process('MX', i)

            elif tokens[0] == '#,' and nb_tokens > 1:
                # we are on a flags line
                self.process('FL', i)

            elif tokens[0] == '#':
                if line == '#': line += ' '
                # we are on a translator comment line
                self.process('TC', i)

            elif tokens[0] == '#.' and nb_tokens > 1:
                # we are on a generated comment line
                self.process('GC', i)

            elif tokens[0] == '#|':
                if nb_tokens < 2:
                    self.process('??', i)
                    continue

                # Remove the marker and any whitespace right after that.
                line = line[2:].lstrip()
                self.current_token = line

                if tokens[1].startswith('"'):
                    # Continuation of previous metadata.
                    self.process('MC', i)
                    continue

                if nb_tokens == 2:
                    # Invalid continuation line.
                    self.process('??', i)

                # we are on a "previous translation" comment line,
                if tokens[1] not in prev_keywords:
                    # Unknown keyword in previous translation comment.
                    self.process('??', i)

                # Remove the keyword and any whitespace
                # between it and the starting quote.
                line = line[len(tokens[1]):].lstrip()
                self.current_token = line
                self.process(prev_keywords[tokens[1]], i)

            else:
                self.process('??', i)

        if self.current_entry:
            # since entries are added when another entry is found, we must add
            # the last entry here (only if there are lines)
            self.instance.append(self.current_entry)
        # before returning the instance, check if there's metadata and if 
        # so extract it in a dict
        firstentry = self.instance[0]
        if firstentry.msgid == '': # metadata found
            # remove the entry
            firstentry = self.instance.pop(0)
            self.instance.metadata_is_fuzzy = firstentry.flags
            key = None
            for msg in firstentry.msgstr.splitlines():
                try:
                    key, val = msg.split(':', 1)
                    self.instance.metadata[key] = val.strip()
                except:
                    if key is not None:
                        self.instance.metadata[key] += '\n'+ msg.strip()
        # close opened file
        if isinstance(self.fhandle, file):
            self.fhandle.close()
        return self.instance

    def add(self, symbol, states, next_state):
        """
        Add a transition to the state machine.

        Keywords arguments:

        ``symbol``
            string, the matched token (two chars symbol).

        ``states``
            list, a list of states (two chars symbols).

        ``next_state``
            the next state the fsm will have after the action.
        """
        for state in states:
            action = getattr(self, 'handle_%s' % next_state.lower())
            self.transitions[(symbol, state)] = (action, next_state)

    def process(self, symbol, linenum):
        """
        Process the transition corresponding to the current state and the
        symbol provided.

        Keywords arguments:

        ``symbol``
            string, the matched token (two chars symbol).

        ``linenum``
            integer, the current line number of the parsed file.
        """
        try:
            (action, state) = self.transitions[(symbol, self.current_state)]
            if action():
                self.current_state = state
        except Exception, exc:
            raise IOError('Syntax error in po file (line %s)' % linenum)

    # state handlers

    def handle_he(self):
        """Handle a header comment."""
        if self.instance.header != '':
            self.instance.header += '\n'
        self.instance.header += self.current_token[2:]
        return 1

    def handle_tc(self):
        """Handle a translator comment."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        if self.current_entry.tcomment != '':
            self.current_entry.tcomment += '\n'
        self.current_entry.tcomment += self.current_token[2:]
        return True

    def handle_gc(self):
        """Handle a generated comment."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        if self.current_entry.comment != '':
            self.current_entry.comment += '\n'
        self.current_entry.comment += self.current_token[3:]
        return True

    def handle_oc(self):
        """Handle a file:num occurence."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        occurrences = self.current_token[3:].split()
        for occurrence in occurrences:
            if occurrence != '':
                try:
                    fil, line = occurrence.split(':')
                    if not line.isdigit():
                        fil  = fil + line
                        line = ''
                    self.current_entry.occurrences.append((fil, line))
                except:
                    self.current_entry.occurrences.append((occurrence, ''))
        return True

    def handle_fl(self):
        """Handle a flags line."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.flags += self.current_token[3:].split(', ')
        return True

    def handle_pp(self):
        """Handle a previous msgid_plural line."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.previous_msgid_plural = \
            unescape(self.current_token[1:-1])
        return True

    def handle_pm(self):
        """Handle a previous msgid line."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.previous_msgid = \
            unescape(self.current_token[1:-1])
        return True

    def handle_pc(self):
        """Handle a previous msgctxt line."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.previous_msgctxt = \
            unescape(self.current_token[1:-1])
        return True

    def handle_ct(self):
        """Handle a msgctxt."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.msgctxt = unescape(self.current_token[1:-1])
        return True

    def handle_mi(self):
        """Handle a msgid."""
        if self.current_state in ['MC', 'MS', 'MX']:
            self.instance.append(self.current_entry)
            self.current_entry = POEntry()
        self.current_entry.obsolete = self.entry_obsolete
        self.current_entry.msgid = unescape(self.current_token[1:-1])
        return True

    def handle_mp(self):
        """Handle a msgid plural."""
        self.current_entry.msgid_plural = unescape(self.current_token[1:-1])
        return True

    def handle_ms(self):
        """Handle a msgstr."""
        self.current_entry.msgstr = unescape(self.current_token[1:-1])
        return True

    def handle_mx(self):
        """Handle a msgstr plural."""
        index, value = self.current_token[7], self.current_token[11:-1]
        self.current_entry.msgstr_plural[index] = unescape(value)
        self.msgstr_index = index
        return True

    def handle_mc(self):
        """Handle a msgid or msgstr continuation line."""
        token = unescape(self.current_token[1:-1])
        if self.current_state == 'CT':
            typ = 'msgctxt'
            self.current_entry.msgctxt += token
        elif self.current_state == 'MI':
            typ = 'msgid'
            self.current_entry.msgid += token
        elif self.current_state == 'MP':
            typ = 'msgid_plural'
            self.current_entry.msgid_plural += token
        elif self.current_state == 'MS':
            typ = 'msgstr'
            self.current_entry.msgstr += token
        elif self.current_state == 'MX':
            typ = 'msgstr[%s]' % self.msgstr_index
            self.current_entry.msgstr_plural[self.msgstr_index] += token
        elif self.current_state == 'PP':
            typ = 'previous_msgid_plural'
            token = token[3:]
            self.current_entry.previous_msgid_plural += token
        elif self.current_state == 'PM':
            typ = 'previous_msgid'
            token = token[3:]
            self.current_entry.previous_msgid += token
        elif self.current_state == 'PC':
            typ = 'previous_msgctxt'
            token = token[3:]
            self.current_entry.previous_msgctxt += token
        # don't change the current state
        return False

# }}}
# class _MOFileParser {{{

class _MOFileParser(object):
    """
    A class to parse binary mo files.
    """

    def __init__(self, mofile, *args, **kwargs):
        """
        Constructor.

        Keyword arguments:

        ``mofile``
            string, path to the mo file or its content

        ``encoding``
            string, the encoding to use, defaults to ``default_encoding``
            global variable (optional).

        ``check_for_duplicates``
            whether to check for duplicate entries when adding entries to the
            file (optional, default: ``False``).
        """
        self.fhandle = open(mofile, 'rb')
        self.instance = MOFile(
            fpath=mofile,
            encoding=kwargs.get('encoding', default_encoding),
            check_for_duplicates=kwargs.get('check_for_duplicates', False)
        )

    def parse(self):
        """
        Build the instance with the file handle provided in the
        constructor.
        """
        # parse magic number
        magic_number = self._readbinary('<I', 4)
        if magic_number == MOFile.LITTLE_ENDIAN:
            ii = '<II'
        elif magic_number == MOFile.BIG_ENDIAN:
            ii = '>II'
        else:
            raise IOError('Invalid mo file, magic number is incorrect !')
        self.instance.magic_number = magic_number
        # parse the version number and the number of strings
        self.instance.version, numofstrings = self._readbinary(ii, 8)
        # original strings and translation strings hash table offset
        msgids_hash_offset, msgstrs_hash_offset = self._readbinary(ii, 8)
        # move to msgid hash table and read length and offset of msgids
        self.fhandle.seek(msgids_hash_offset)
        msgids_index = []
        for i in range(numofstrings):
            msgids_index.append(self._readbinary(ii, 8))
        # move to msgstr hash table and read length and offset of msgstrs
        self.fhandle.seek(msgstrs_hash_offset)
        msgstrs_index = []
        for i in range(numofstrings):
            msgstrs_index.append(self._readbinary(ii, 8))
        # build entries
        for i in range(numofstrings):
            self.fhandle.seek(msgids_index[i][1])
            msgid = self.fhandle.read(msgids_index[i][0])
            self.fhandle.seek(msgstrs_index[i][1])
            msgstr = self.fhandle.read(msgstrs_index[i][0])
            if i == 0: # metadata
                raw_metadata, metadata = msgstr.split('\n'), {}
                for line in raw_metadata:
                    tokens = line.split(':', 1)
                    if tokens[0] != '':
                        try:
                            metadata[tokens[0]] = tokens[1].strip()
                        except IndexError:
                            metadata[tokens[0]] = ''
                self.instance.metadata = metadata
                continue
            # test if we have a plural entry
            msgid_tokens = msgid.split('\0')
            if len(msgid_tokens) > 1:
                entry = self._build_entry(
                    msgid=msgid_tokens[0],
                    msgid_plural=msgid_tokens[1],
                    msgstr_plural=dict((k,v) for k,v in enumerate(msgstr.split('\0')))
                )
            else:
                entry = self._build_entry(msgid=msgid, msgstr=msgstr)
            self.instance.append(entry)
        # close opened file
        self.fhandle.close()
        return self.instance
    
    def _build_entry(self, msgid, msgstr=None, msgid_plural=None,
                     msgstr_plural=None):
        msgctxt_msgid = msgid.split('\x04')
        if len(msgctxt_msgid) > 1:
            kwargs = {
                'msgctxt': msgctxt_msgid[0],
                'msgid'  : msgctxt_msgid[1],
            }
        else:
            kwargs = {'msgid': msgid}
        if msgstr:
            kwargs['msgstr'] = msgstr
        if msgid_plural:
            kwargs['msgid_plural'] = msgid_plural
        if msgstr_plural:
            kwargs['msgstr_plural'] = msgstr_plural
        return MOEntry(**kwargs)

    def _readbinary(self, fmt, numbytes):
        """
        Private method that unpack n bytes of data using format <fmt>.
        It returns a tuple or a mixed value if the tuple length is 1.
        """
        bytes = self.fhandle.read(numbytes)
        tup = struct.unpack(fmt, bytes)
        if len(tup) == 1:
            return tup[0]
        return tup

# }}}
# class TextWrapper {{{

class TextWrapper(textwrap.TextWrapper):
    """
    Subclass of textwrap.TextWrapper that backport the
    drop_whitespace option.
    """
    def __init__(self, *args, **kwargs):
        drop_whitespace = kwargs.pop('drop_whitespace', True) 
        textwrap.TextWrapper.__init__(self, *args, **kwargs)
        self.drop_whitespace = drop_whitespace

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]

        Wrap a sequence of text chunks and return a list of lines of
        length 'self.width' or less.  (If 'break_long_words' is false,
        some lines may be longer than this.)  Chunks correspond roughly
        to words and the whitespace between them: each chunk is
        indivisible (modulo 'break_long_words'), but a line break can
        come between any two chunks.  Chunks should not have internal
        whitespace; ie. a chunk is either all whitespace or a "word".
        Whitespace chunks will be removed from the beginning and end of
        lines, but apart from that whitespace is preserved.
        """
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)

        # Arrange in reverse order so items can be efficiently popped
        # from a stack of chucks.
        chunks.reverse()

        while chunks:

            # Start the list of chunks that will make up the current line.
            # cur_len is just the length of all the chunks in cur_line.
            cur_line = []
            cur_len = 0

            # Figure out which static string will prefix this line.
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            # Maximum width for this line.
            width = self.width - len(indent)

            # First chunk on line is whitespace -- drop it, unless this
            # is the very beginning of the text (ie. no lines started yet).
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                l = len(chunks[-1])

                # Can at least squeeze this chunk onto the current line.
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                # Nope, this line is full.
                else:
                    break

            # The current line is full, and the next chunk is too big to
            # fit on *any* line (not just this one).
            if chunks and len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)

            # If the last chunk on this line is all whitespace, drop it.
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                del cur_line[-1]

            # Convert current line back to a string and store it in list
            # of all lines (return value).
            if cur_line:
                lines.append(indent + ''.join(cur_line))

        return lines

# }}}
# function wrap() {{{

def wrap(text, width=70, **kwargs):
    """
    Wrap a single paragraph of text, returning a list of wrapped lines.
    """
    if sys.version_info < (2, 6):
        return TextWrapper(width=width, **kwargs).wrap(text)
    return textwrap.wrap(text, width=width, **kwargs)

#}}}
