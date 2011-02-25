#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VERSION = '1.0'

"""csub {0} - utility to synchronize subtitle files (actually: *.srt)

# Copyright (C) 2010  Marco Chieppa (aka crap0101)
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc., 
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.    

Changelog (2010-07-11):
    * using tempfile for creation of a backup file to avoid
      accidental deletion of the source sub when the input file
      and the output file are the same.
Examples:
  # reading from stdin and output to stdout ans ass/ssa sub:
  ~$ ./prog_name --minutes 3 --seconds -44 --milliseconds -378 -num 2 -t ass
  # read a srt file from 'file_sub.srt' to 'newfile.srt':
  ~$ ./prog_name -t srt -M -1 -S 4 -i film_sub.srt -o newfile.srt
""".format(VERSION)

#################
# I M P O R T S #
#################

import os
import re
import sys
import math
import operator
import itertools
import warnings
from tempfile import mkstemp
from optparse import OptionParser, OptionValueError
from string import Template

#####################
# F U N C T I O N S #
#####################


def numslice(n, i, keep_sign=False):
    '''
    Return the slice of the *i* most significant digs of *n*
    for *i* > 0 or the less significant digits for *i* < 0 .
    Preserve the sign if *keep_sign* is a true value (default: False).
    '''
    n, sign_op = (n, operator.pos) if n > 0 else (abs(n), operator.neg)
    if not (i and n):
        return sign_op(n) #raise ValueError('invalid number: %d' % i)
    b = int(math.log10(n)) + 1
    if abs(i) > b:
        return sign_op(n) #raise ValueError('invalid number: %d' % i)
    m, g = ((b-i), 0) if i > 0 else (abs(i), 1)
    return sign_op(divmod(n, 10**m)[g]) if keep_sign else divmod(n, 10**m)[g]


def check_ms (option, opt_str, value, parser, **kwords):
    if not (-999 <= value <= 999):
        raise OptionValueError("option `%s` must be in range -999..999"
                               % (opt_str,))
    setattr(parser.values, kwords['opt_dest'], value)


def iterdec (multicall=False):
    """Decorator used on the line's ckeck methods. """
    def _iterdec1 (function):
        def _iterdec2 (*args, **kwords):
            res = function(*args, **kwords)
            if multicall and res:
                return res, False
            return res, True
        return _iterdec2
    return _iterdec1


def TempFileManager (methods):
    """Decorator for temp files. """
    def inner1 (cls):
        def inner2 (file_stream, options=None):
            if file_stream and file_stream != sys.stdin:
                return cls(file_stream, options)
            dict_ = {'_fake': True}
            for method in methods:
                dict_[method] = lambda *args: None
                dict_[method].__name__ = method
            return type(cls.__name__, (object,), dict_)()
        return inner2
    return inner1


#################
# C L A S S E S #
#################

@TempFileManager(('close', 'read', 'seek', 'write_back'))
class TempFile:
    """Class to manage temp file (using tmpfile's mkstemp). """
    def __init__ (self, in_file, options=None):
        self.opts = {'suffix': '.csub-backup',
                     'prefix': 'subtitle_',
                     'text': True,}
        self.opts.update(options or {})
        self.in_file = in_file
        self.fd, self.filepath = mkstemp(**self.opts)
        with open(self.in_file, 'rb') as _in:
            self.fd_max_pos = os.write(self.fd, _in.read())
        self.seek(0, 0)

    def close (self):
        os.close(self.fd)

    def read (self):
        return os.read(self.fd, self.fd_max_pos)

    def seek (self, pos, how):
        return os.lseek(self.fd, pos, how)

    def write_back (self):
        with open(self.in_file, 'wb') as _in:
            _in.write(self.read())
            _in.truncate()


class BadFormatError (Exception):
    """Base class for formatting errors. """
    pass


class MismatchTimeError (BadFormatError):
    """Raised when a malformed time is found. """

    def __init__ (self, message):
        super(MismatchTimeError, self).__init__()
        self.message = message

    def __str__ (self):
        return "Invalid time format: %s" % self.message


class IndexNumError (BadFormatError):
    """Raised when a malformed subs identifier is found. """

    def __init__ (self, message):
        super(IndexNumError, self).__init__()
        self.message = message

    def __str__ (self):
        return "Invalid subtitle number: %s" % repr(self.message)


class IncompleteBlockError (Warning):
    """Raised for incomplete block at the EOF (e.g. no newline). """

    def __init__ (self, message):
        super(IncompleteBlockError, self).__init__()
        self.message = message

    def __str__ (self):
        return self.message
    

class GetFunc:
    """ Help class to iterate over the line's check methods. """

    def __init__ (self, cycle):
        self.cycle = cycle
        self.function = next(cycle)

    def __call__ (self, *args, **kwords):
        res, change = self.function(*args, **kwords)
        if change:
            self.function = next(self.cycle)
        return res


class Subtitle:
    """Base class implementing common function for time manipulation
    and subtitles formatting.
    """
    def __init__ (self, str_format='', re_pattern='.*'):
        self.STRING_FORMAT = str_format
        self.RE_MATCH_TIME = re.compile(re_pattern)
        self.RE_MATCH_NUMBER = re.compile('^-{0,1}\d+$')
        self.MAX_H = 3600
        self.MAX_MIN = 60
        self.MAX_HNDRS = 100 # for ssa/ass
        self.MAX_MS = 1000
        self.delta_hour = self.delta_min = self.delta_sec = 0
        self.delta_ms = self.delta_sub_num = 0
        self.IS_BLOCK = True
        self.IS_WARN = False
        self.IN_RANGE = True
        self.check_range_to_edit = self.edit_range()
        self.actual_numline = 0

    @staticmethod
    def edit_range(start=None, stop=None):
        start = 1 if start is None else start
        stop = float('+inf') if stop is None else stop
        def is_edit(number):
            return number >= start and number < stop
        return is_edit
    
    def set_delta (self, hour=0, min_=0, sec=0, ms=0, sub_number=0):
        """Set time's attribute."""
        self.delta_hour = hour
        self.delta_min = min_
        self.delta_sec = sec
        self.delta_ms = ms
        self.delta_sub_num = sub_number

    def set_subs_range(self, start=None, end=None):
        """Set blocks' range to edit, from `start' to `end' (excluded)."""
        self.check_range_to_edit = self.edit_range(start, end)

    def make_iter_blocks (self, *methods):
        """Returns an itertools.cycle object for *methods. """
        return itertools.cycle(methods)

    def match_time (self, string_time):
        """Check the time-line and return the matched values
        or raise MismatchTimeError.
        """
        matched = re.match(self.RE_MATCH_TIME, string_time)
        if matched is None:
            raise MismatchTimeError("'%s' (in %s)" % (string_time, "match_time"))
        return matched

    def new_sub_num (self, num_str):
        """Check the subtitle's number and return it
        or raise IndexNumError.
        """
        matched = re.match(self.RE_MATCH_NUMBER, num_str.rstrip())
        if matched is not None:
            sub_num = int(matched.group(0))
            if self.check_range_to_edit(sub_num):
                self.IN_RANGE = True
                return sub_num + self.delta_sub_num
            else:
                self.IN_RANGE = False
                return sub_num
        if not self.unsafe_number_mode:
            raise IndexNumError(num_str)
        else:
            return int(num_str)

    def new_time_tuple (self, hour, min_, sec, ms):
        """Returns a tuple of (seconds, ms)
        updated according to the delta.
        """
        total_sec = sum(((hour + self.delta_hour) * self.MAX_H,
                         (min_ + self.delta_min) * self.MAX_MIN,
                         sec + self.delta_sec))
        new_ms = ms + self.delta_ms
        if new_ms < 0 or new_ms >= self.MAX_MS:
            sec_to_add, new_ms = divmod(new_ms, self.MAX_MS)
            total_sec += sec_to_add
        return total_sec, abs(new_ms)

    def parse (self, lines, itertools_cycle_iterator):
        """Iterate over subtitle's ``lines''"""
        get_func = GetFunc(itertools_cycle_iterator)
        for line, self.actual_numline in zip(lines, itertools.count(1)):
            yield "%s\n" % get_func(line)

    def times_from_secs (self, total_sec):
        """Returns a tuple of (hour, minutes, secs)
        from a time expressed in seconds.
        """
        hour, m = divmod(total_sec, self.MAX_H)
        return hour, m / self.MAX_MIN, total_sec % self.MAX_MIN


class AssSub (Subtitle):
    """Class to manage *.ass/*.ssa subtitle. Inherit from Subtitle."""
    def __init__ (self, file_in, file_out, unsafe_time_mode=False):
        """`file_in' and `file_out' must be file-like objects."""
        reg = '(^Dialogue: \d+),(\d{1}:\d{2}:\d{2}([:\.])\d{2}),(\d{1}:\d{2}:\d{2}([:.])\d{2}),(.*$)'
        reg_unsafe = '(^Dialogue: \d+),(-{0,1}\d+:\d{2}:\d{2}([:\.])\d{2}),(-{0,1}\d+:\d{2}:\d{2}([:.])\d{2}),(.*$)'
        time_reg = '(\d{1}):(\d{2}):(\d{2})[:\.](\d{2})'
        time_reg_unsafe = '(-{0,1}\d+):(\d{2}):(\d{2})[:\.](\d{2})'
        # Why these regex? well...
        # The spec for ass/ssa file talk about a time format like
        # 0:00:00:00  (so, *1* digit for hours and the colon as divider)
        # ie. Hrs:Mins:Secs:hundredths
        # BUT... some ass/ssa file use dot between Secs and hundredths,
        # and many player accept this; so, we want to preserve the original sep.
        self.reg = (re.compile(reg) if not unsafe_time_mode
                    else re.compile(reg_unsafe))
        self.time_reg = (re.compile(time_reg) if not unsafe_time_mode
                                        else re.compile(time_reg_unsafe))
        super(AssSub, self).__init__()
        self.file_in = file_in
        self.file_out = file_out
        self.actual_numline = 0
        self.MAX_MS = self.MAX_HNDRS
        # NOTE: since ass/ssa use 2-digit precision for fraction of seconds
        # *MAX_MS* is used as an alias for *MAX_HNDRS* and *self.delta_ms*
        # used in various methods of the base class refer to hundreds, not
        # milliseconds (to avoid rewrite methos in the base class).
        
    def new_time(self, time_string, sec_sep):
        h, m, s, hndrs = list(map(int, self.time_reg.match(time_string).groups()))
        total_secs, hndrs = self.new_time_tuple(h, m, s, hndrs)
        h, m, s = self.times_from_secs(total_secs)
        return "%d:%02d:%02d%s%02d" % (h, m, s, sec_sep, hndrs) #numslice(hndrs, 2))

    def parse_line (self, line):
        """Fields are:
          Marked, Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
        we care about fields 1 and 2.
        """
        line = line.rstrip()
        if line.startswith('Dialogue:'):
            try:
                match = self.reg.match(line)
                init, start, start_sep, end, end_sep, rest = match.groups()
                new_start = self.new_time(start, start_sep)
                new_end = self.new_time(end, end_sep)
                return ','.join((init, new_start, new_end, rest))
            except ValueError as err:
                raise MismatchTimeError("(%s) Something went wrong "
                                        "computing this line: %s" % (err, line))
            except AttributeError as err:
                raise MismatchTimeError("You probably need to "
                                        "--back-to-the-future\n"
                                        "ERR LINE IS: %s" % line)            
        return line

    def set_delta(self, hour=0, min_=0, sec=0, hndrs=0, *not_used):
        super(AssSub, self).set_delta(hour, min_, sec)
        self.delta_ms = hndrs
    
    def main (self):
        for self.actual_numline, line in zip(
            itertools.count(1), self.file_in):
            self.file_out.write("%s\n" % self.parse_line(line))

        
class SrtSub (Subtitle):
    """Class to manage *.srt subtitle. Inherit from Subtitle."""

    def __init__ (self, file_in, file_out, unsafe_time_mode=False, unsafe_number_mode=False):
        """`file_in' and `file_out' must be file-like objects."""
        self.time_sep = " --> "
        self.string_format = "%02d:%02d:%02d,%03d"
        reg_safe = r'^(-{0,1}\d{2,}):(\d{2}):(\d{2}),(\d{3})$'
        reg_unsafe = r'^(-{0,1}\d{1,}):(\d{2}):(\d{2}),(\d{3})$'
        self.re_pattern = reg_unsafe if unsafe_time_mode else reg_safe
        self.unsafe_number_mode = unsafe_number_mode
        super(SrtSub, self).__init__(self.string_format, self.re_pattern)
        self.file_in = file_in
        self.file_out = file_out

    @iterdec()
    def num_block (self, nums_string):
        """Check the subtitle's number identifier lines. """
        self.IS_BLOCK = True
        return self.new_sub_num(nums_string)

    @iterdec()
    def time_block (self, time_string):
        """Check the time lines. """
        if not self.IN_RANGE:
            return time_string.rstrip()
        try:
            start, end = list(map(str.strip, time_string.split(self.time_sep)))
        except ValueError:
            raise MismatchTimeError("[at line %d] '%s' (in %s)"
                 % (self.actual_numline, time_string, "time_block"))
        h, m, s, ms = list(map(int, self.match_time(start).group(1, 2, 3, 4)))
        sec, ms = self.new_time_tuple(h, m, s, ms)
        nh, nm, ns = self.times_from_secs(sec)
        new_start = self.string_format % (nh, nm, ns, ms)
        h, m, s, ms = list(map(int, self.match_time(end).group(1, 2, 3 , 4)))
        sec, ms = self.new_time_tuple(h, m, s, ms)
        nh, nm, ns = self.times_from_secs(sec)
        new_end = self.string_format % (nh, nm, ns, ms)
        return self.time_sep.join((new_start, new_end))

    @iterdec(multicall=True)
    def text_block (self, line):
        """Returns the text line rstripped (no checks needed). """
        self.IS_BLOCK = False
        return line.rstrip()

    def main (self):
        """Doing the job. """
        cycle = self.make_iter_blocks(self.num_block,
                                      self.time_block,
                                      self.text_block)
        new_lines = self.parse(self.file_in, cycle)
        self.file_out.writelines(new_lines)
        if self.IS_BLOCK and self.IS_WARN:
            warnings.warn("Incomplete block at EOF", IncompleteBlockError)


###########
# M A I N #
###########

if __name__ == '__main__':
    in_file = sys.stdin 
    out_file = sys.stdout
    samefile = False
    tmpfile = TempFile(None)

    parser = OptionParser(version="csub %s" % VERSION)
    parser.add_option("--info", dest="info", action="store_true",
                      help="print informations about the program and exit.")
    parser.add_option("-t", "--type",type="string",
                      dest="subtitle_type", metavar="TYPE",
                      help="subtitle file type: ass, ssa, srt.")
    parser.add_option("-o", "--output-file",type="string",
                      dest="outfile", metavar="FILE",
                      help="write the subtitle in FILE (default: stdout).")
    parser.add_option("-i", "--input-file", type="string",
                      dest="infile", metavar="FILE",
                      help="read the subtitle from FILE (default: stdin).")
    parser.add_option("-S", "--seconds", type="int",
                      default=0, dest="sec", metavar="NUMBER",
                      help="change the seconds values by NUMBER.")
    parser.add_option("-M", "--minutes", type="int",
                      dest="min", default=0, metavar="NUMBER",
                      help="change the minutes values by NUMBER.")
    parser.add_option("-H", "--hours", type="int",
                      dest="hour", default=0, metavar="NUMBER",
                      help="change the hours values by NUMBER.")
    parser.add_option("-m", "--milliseconds", type="int", action="callback",
                      callback_kwargs={'opt_dest':"ms",}, callback=check_ms,
                      metavar="NUMBER", dest="ms", default=0,
                      help="change the milliseconds values by NUMBER. "
                      "(NOTE: this value must be in range -999..999).")
    parser.add_option("-n", "--num", type="int", dest="num",
                      default=0, metavar="NUMBER",
                      help="change the progressive subtitle number by NUMBER. "
                      "(only for srt).")
    parser.add_option("-r", "--range", type="str",
                      dest="range", default=':', metavar="START:END",
                      help="apply changes only for subs between START"
                      " and END (excluded). (only for srt).")
    parser.add_option("-b", "--back-to-the-future", action="store_true",
                      dest="unsafe_time_mode", default=False,
                      help="unsafe time mode. Don't get any errors if "
                      " timecode become negative.")
    parser.add_option("-B", "--back-to-the-block", action="store_true",
                      dest="unsafe_number_mode", default=False,
                      help="unsafe number mode. Don't get any errors if "
                      "sub's numbers became negative.  (only for srt).")
    parser.add_option("-w", "--warn", action="store_true", dest="is_warn",
                      default=False, help="enable warnings.")

    opts, args = parser.parse_args()
    if opts.info:
        print(__doc__)
        sys.exit(0)
    if args:
         parser.error("Error: unknown argument(s) %s" % args)
    if opts.infile == opts.outfile and all((opts.infile, opts.outfile)):
        tmpfile = TempFile(opts.infile)
        in_file = open(tmpfile.filepath, 'r')
        out_file = open(opts.infile, 'w')
    else:
        if opts.infile:
            in_file = open(opts.infile, "r")
        if opts.outfile:
            out_file = open(opts.outfile, "w")
    # temporary ugly if/elif:
    if not opts.subtitle_type:
        parser.error("subtitle type (-t/--type) must be specified!")
    if opts.subtitle_type in ('ass', 'ssa'):
        newsub = AssSub(in_file, out_file, opts.unsafe_time_mode)
    elif opts.subtitle_type == 'srt':
        newsub = SrtSub(in_file, out_file,
                        opts.unsafe_time_mode, opts.unsafe_number_mode)
        start_sub, end_sub = opts.range.split(':')
        newsub.set_subs_range(int(start_sub) if start_sub else None,
                              int(end_sub) if end_sub else None)
    newsub.set_delta(opts.hour, opts.min, opts.sec, opts.ms, opts.num)
    newsub.IS_WARN = opts.is_warn
    opt_err = Template('options $what not available with ass/ssa subtitles\n')
    if opts.subtitle_type in ('ass', 'ssa'):
        if opts.range != ':':
            parser.error(opt_err.substitute(what='-r/--range'))
        if opts.num:
            parser.error(opt_err.substitute(what='-n/--num'))
        if opts.unsafe_number_mode:
            parser.error(opt_err.substitute(what='-B/--back-to-the-block'))
    try:
        newsub.main()
    except (BadFormatError, MismatchTimeError, IndexNumError) as e:
        sys.stderr.write("%s: [at line %d] %s\n"
             % (e.__class__.__name__, newsub.actual_numline, str(e)))
        in_file.close()
        out_file.close()
        tmpfile.write_back()
    except Exception as e:
        in_file.close()
        out_file.close()
        tmpfile.write_back()
        ue_msg = "\nUnknow error! surely a bug. Shit!\nException is"
        sys.stderr.write("%s: [at line %d] %s\n\n"
                         % (ue_msg, newsub.actual_numline, str(e)))
    in_file.close()
    out_file.close()
