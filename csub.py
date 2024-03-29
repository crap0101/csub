#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VERSION = '1.4_20160912'

"""csub {0} - utility to synchronize subtitle files

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

Requirements:
  - Python >= 3

Supported formats:
  - SubRip (*.srt)
  - (Advanced) SubStation Alpha (*.ass, *.ssa)
  - MicroDVD (*.sub)

Examples:
  # reading from stdin and output to stdout an ass/ssa sub:
  ~$ ./prog_name --minutes 3 --seconds -44 --milliseconds -378 -num 2 -t ass
  # read a srt file from 'file_sub.srt' to 'newfile.srt':
  ~$ ./prog_name -t srt -M -1 -S 4 -i film_sub.srt -o newfile.srt
""".format(VERSION)

#################
# I M P O R T S #
#################

import atexit
import argparse
import codecs
import itertools
import math
import operator
import os
import re
from string import Template
import sys
import tempfile
import warnings

#############
# CONSTANTS #
#############

OPT_RANGE = ':'

#####################
# F U N C T I O N S #
#####################

def clean_backup (tmpfile):
    if tmpfile.filepath:
        try:
            os.remove(tmpfile.filepath)
        except Exception as err:
            warnings.warn("Warning: can't remove backup file '{}': {}".format(
                    tmpfile.filepath, err))

def close_files(files):
    """Close anf flush any file in *files* if not a tty."""
    for file in files:
        if not file.isatty():
            file.close()

def iterdec (multicall=False):
    """Decorator used on the line's ckeck methods."""
    def _iterdec1 (function):
        def _iterdec2 (*args, **kwords):
            res = function(*args, **kwords)
            if multicall and res:
                return res, False
            return res, True
        return _iterdec2
    return _iterdec1

def get_stretch (s):
    return [(int(x) if x else 0) for x in s.strip().split(':')]

def numslice(n, i, keep_sign=False):
    '''
    Return the slice of the *i* most significant digs of *n*
    for *i* > 0 or the less significant digits for *i* < 0 .
    Preserve the sign if *keep_sign* is a true value (default: False).
    '''
    n, sign_op = (n, operator.pos) if n > 0 else (abs(n), operator.neg)
    if not (i and n):
        return sign_op(n)
    b = int(math.log10(n)) + 1
    if abs(i) > b:
        return sign_op(n)
    m, g = ((b-i), 0) if i > 0 else (abs(i), 1)
    return sign_op(divmod(n, 10**m)[g]) if keep_sign else divmod(n, 10**m)[g]

def save_on_error(infile, outfile, tmpfile):
    """Save files on error, to preserve data."""
    close_files((in_file, out_file))
    tmpfile.write_back()
    tmpfile.close()

def skip_bytes(stream, nbytes):
    """Read nbytes from stream and return them."""
    return stream.read(nbytes)

def TempFileManager (methods):
    """Decorator for temp files."""
    def inner1 (cls):
        def inner2 (file_stream, options=None):
            if file_stream and file_stream != sys.stdin:
                return cls(file_stream, options)
            dict_ = {'filepath': None}
            for method in methods:
                dict_[method] = lambda *args: None
                dict_[method].__name__ = method
            return type(cls.__name__, (object,), dict_)()
        return inner2
    return inner1


def get_parser():
    """Return an argparse's parser object."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--info", dest="info", action="store_true",
                        help="print informations about the program and exit.")
    parser.add_argument(
        '--version', action='version', version='csub {}'.format(VERSION))
    # I/O options
    io_parser = parser.add_argument_group('Input and Output')
    io_parser.add_argument("-e", "--encoding",
        dest="encoding", metavar="NAME", default='utf-8-sig', help="""
        subtitle encoding to use for reading and writing files.
        Must match the input file's encoding (default to utf-8-sig).
        If you want to get rid of the BOM in such a marked files use
        a bare 'utf-8' codec and the -s/--skip option (like -e utf-8 -s1)
        to delete it.""")
    io_parser.add_argument("-E", "--encode-error",
        dest='enc_err', default='strict', metavar="NAME",
        choices=('strict', 'replace', 'ignore'), help="""
        specifies how encoding and decoding errors are to be handled.
        Pass 'strict' to raise an error if there is an encoding error,
        'ignore' to ignore errors (Note that ignoring encoding errors can
        lead to data loss) or 'replace' to insert a replacement marker
        (such as '?') where there is malformed data. Default to 'strict'.""")
    io_parser.add_argument("-i", "--input-file",
        dest="infile", metavar="FILE",
        help="read the subtitle from FILE (default: stdin).")
    io_parser.add_argument("-o", "--output-file",
        dest="outfile", metavar="FILE",
        help="write the subtitle in FILE (default: stdout).")
    io_parser.add_argument("-O", "--same-file",
        dest="same_file", metavar="FILE",
        help="use %(metavar)s as both input and output file.")
    io_parser.add_argument("-s", "--skip-bytes",
        dest="skip_bytes", type=int, metavar="NUM",
        help="""skip the first NUM file's bytes (must be an integer >= 0).
        Required in certain situations, e.g. to skip use(full|less) BOM.""")
    io_parser.add_argument("-t", "--type",
        dest="subtitle_type", metavar="TYPE",
        choices=('ass','ssa', 'srt', 'sub','microdvd'),
        help="subtitle file type: (ass|ssa, srt, sub|microdvd).")
    # subtiles options
    s_parser = parser.add_argument_group('Subtitle Options')
    srt_parser = parser.add_argument_group('Subrip (*.srt) Specific Options')
    ass_parser = parser.add_argument_group(
        '(Advanced) SubStation Alpha (*.ass, *.ssa) Specific Options')
    mdv_parser = parser.add_argument_group('MicroDVD (*.sub) Specific Options')
    ## all subtitles
    s_parser.add_argument("-b", "--back-to-the-future",
        action="store_true", dest="unsafe_time_mode", default=False,
        help="unsafe time mode. Don't get errors for negative timecodes.")
    s_parser.add_argument('-c', '--change-framerate',
        dest='change_framerate', default=False, nargs=2, type=float,
        metavar=('OLD', 'NEW'), help='change framerate from OLD to NEW')
    s_parser.add_argument("-H", "--hours",
        type=int, dest="hour", default=0, metavar="NUMBER",
        help="change the hours values by NUMBER.")
    s_parser.add_argument("-M", "--minutes",
        type=int, dest="min", default=0, metavar="NUMBER",
        help="change the minutes values by NUMBER.")
    s_parser.add_argument("-m", "--milliseconds",
        dest="ms", default=0, metavar="NUMBER", choices=range(-999, 1000),
        type=int, help="""change the milliseconds values by NUMBER.
        (NOTE: this value must be in range -999..999).""")
    s_parser.add_argument("-r", "--range",
        dest="range", default=OPT_RANGE, metavar="START:END", help="""
        apply changes only between START and END (excluded).
        Both START and END can be omitted, in such case changes are applied
        from the beginning (for START) to the end (for END).
        START and END must be integer values, and their meaning changes
        in relation of the kind of subtitle processed. For SubRip subtitles
        represents the subtitle's block number, for microDVD subtitles
        are understood as frames, whereas for SubStation Alpha subtitles
        are treated as seconds.""")
    s_parser.add_argument("-S", "--seconds",
        type=int, default=0, dest="sec", metavar="NUMBER",
        help="change the seconds values by NUMBER.")
    s_parser.add_argument("--stretch", dest='stretch',
        default=':', metavar='LSHIFT:RSHIFT', help="""
        stretch subs time by the given pair of colon-separated values
        (can be omitted, evaluate to zero in this case).
        The first argument is the amount by which the subtitle's start time
        will be shifted ahead (so, a negative value cause backwards shifting;
        the 2nd is the amount by which the subtitle's end time will be shifted
        ahead (a negative value will cause a backwards shifting).
        NOTES on START and END values:
            used with a subrip (*.srt) subtitle are understood as expressed
            in milliseconds, for microDVD subtitle (*.sub) are understood
            as the number of frames to shift, while with SubStation Alpha
            subtitles (*.ass, *.ssa) are understood as centiseconds.""")
    ## srt
    srt_parser.add_argument("-B", "--back-to-the-block",
        action="store_true", dest="unsafe_number_mode", default=False,
        help="unsafe number mode. Don't get errors for negative block nums.")
    '''srt_parser.add_argument("-I", "--ignore-extra",
        action="store_true", dest='ignore_extra', default=False,
        help="""ignore extra informations in the time line (like sub position,
        style, ecc. These informations are extensions of the original subrip
        format, so are normally treated as errors; you must use this option
        for parsing such a subtitles.
        NOTE: Those informations are not kept in the new file.""")'''
    srt_parser.add_argument("-n", "--num",
        type=int, dest="num", default=0, metavar="NUMBER",
        help="change the progressive subtitle number by NUMBER.")
    srt_parser.add_argument("-N", "--make-progressive-num-blocks",
        type=int, dest="prog_sub_num", default=None, metavar="NUMBER",
        help="""Change *all* subtitle numbers in progression,
        starting from NUMBER. Conflicts with options -r and -n, cannot be
        used at the same time.""")
    srt_parser_extra = srt_parser.add_mutually_exclusive_group()
    srt_parser_extra.add_argument("-I", "--ignore-extra",
        action="store_true", dest='ignore_extra', default=False,
        help="""ignore extra informations in the time line (like sub position,
        style, etc.). These informations are extensions of the original subrip
        format, so are normally treated as errors; you must use this option
        for parsing such a subtitles.
        NOTE: Those informations are not kept in the new file.""")
    srt_parser_extra.add_argument("-p", "--preserve-extra",
        action="store_true", dest='preserve_extra', default=False,
        help="""preserve extra informations in the time line (like sub position,
        style, etc.).""")
    ## microDVD
    mdv_parser.add_argument("-f", "--delta-frames",
        type=int, default=0, dest="delta_frames", metavar="NUMBER",
        help="change the frames values by NUMBER")
    mdv_parser.add_argument("-F", "--frames",
        type=int, default=25, dest="frames", metavar="NUMBER",
        help="movie's frame rate (eg. 25, 29.97, 23.976) (default: 25.")
    # other options
    m_parser = parser.add_argument_group('Misc Options')
    m_parser.add_argument("-T", "--tempdir",
        dest="tempdir", metavar='PATH', default=tempfile.gettempdir(),
        help="""Set the temporary directory (must exists) where store backup
        files (default '%(default)s').""")
    m_parser.add_argument("-w", "--warn",
        action="store_true", dest="is_warn", default=False,
        help="enable warnings.")
    return parser


#################
# C L A S S E S #
#################

@TempFileManager(('close', 'closed', 'isatty', 'read', 'seek', 'write_back'))
class TempFile:
    """Class to manage temp file (using tmpfile's mkstemp)."""
    def __init__ (self, in_file, options=None):
        # NOTE: opts used in the test suite to remove backup files,
        # if change here, change there too.
        self.opts = {'suffix': '.csub-backup',
                     'prefix': 'subtitle_',
                     'text': True,}
        self.opts.update(options or {})
        self.in_file = in_file
        self.fd, self.filepath = tempfile.mkstemp(**self.opts)
        with open(self.in_file, 'rb') as _in:
            self.fd_max_pos = os.write(self.fd, _in.read())
        self.seek(0, 0)
        self._closed = False

    @property
    def closed (self):
        return self._closed
    
    def close (self):
        os.close(self.fd)
        self._closed = True

    def isatty(self):
        return os.isatty(self.fd)

    def read (self):
        return os.read(self.fd, self.fd_max_pos)

    def seek (self, pos, how):
        return os.lseek(self.fd, pos, how)

    def write_back (self):
        self.seek(0, 0)
        with open(self.in_file, 'wb') as _in:
            _in.write(self.read())


class BadFormatError (Exception):
    """Base class for formatting errors."""
    pass


class MismatchTimeError (BadFormatError):
    """Raised when a malformed time is found."""
    def __init__ (self, message):
        super().__init__()
        self.message = message
    def __str__ (self):
        return "Invalid time format: {}".format(self.message)


class IndexNumError (BadFormatError):
    """Raised when a malformed subs identifier is found."""
    def __init__ (self, message):
        super().__init__()
        self.message = message
    def __str__ (self):
        return "Invalid subtitle number: {!r}".format(self.message)


class IncompleteBlockError (Warning):
    """Raised for incomplete block at the EOF (e.g. no newline)."""
    def __init__ (self, message):
        super().__init__()
        self.message = message
    def __str__ (self):
        return self.message


class GetFunc:
    """Help class to iterate over the line's check methods."""
    def __init__ (self, cycle):
        self.cycle = cycle
        self.function = next(cycle)
    def __call__ (self, *args, **kwords):
        res, change = self.function(*args, **kwords)
        if change:
            self.function = next(self.cycle)
        return res


class Subtitle:
    """
    Base class implementing common functions for time manipulation
    and subtitles formatting.
    """
    def __init__ (self, str_format='', re_pattern='.*', output_line_format='{}\n'):
        self.set_delta()
        self.STRING_FORMAT = str_format
        self.RE_MATCH_TIME = re.compile(re_pattern)
        self.RE_MATCH_NUMBER = re.compile('^-{0,1}\d+$')
        self._delete_mode = False
        self.OUTPUT_LINE_FORMAT = output_line_format
        self.OUTPUT_LINE_FORMAT_DEL = ''
        self.MAX_H = 3600.0
        self.MAX_MIN = 60.0
        self.MAX_HNDRS = 100.0 # for SubStation Alpha
        self.MAX_MS = 1000.0
        self.delta_hour = self.delta_min = self.delta_sec = 0.0
        self.delta_ms = 0.0
        self.delta_framerate = 1.0
        self.delta_sub_num = 0
        self.IS_BLOCK = True
        self.IS_WARN = False
        self.IN_RANGE = True
        self.check_range_to_edit = self.edit_range()
        self.actual_numline = 0
        self.stretch_left = self.stretch_right = 0.0

    @property
    def delete_mode (self):
        return self._delete_mode
    @delete_mode.setter
    def delete_mode (self, bool_val):
        self._delete_mode = bool_val
            
    @property
    def output_line_fmt (self):
        return (self.OUTPUT_LINE_FORMAT,
                self.OUTPUT_LINE_FORMAT_DEL)[self.IN_RANGE and self.delete_mode]
    @property
    def stretch (self):
        return self.stretch_left, self.stretch_right
    @stretch.setter
    def stretch (self, pair):
        self.stretch_left, self.stretch_right = pair

    def change_framerate (self, old, new):
        self.delta_framerate = float(new)/float(old)

    @staticmethod
    def edit_range(start=None, stop=None):
        """
        Return a function giving one argument (a number)
        used to check if the given number (the subtitle's index number
        in this case) is in the [start, stop] range and must be edited.
        """
        start = float('-inf') if start is None else start
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

    def set_subs_range (self, start=None, end=None):
        """Set blocks range to edit, from `start' to `end' (excluded)."""
        self.check_range_to_edit = self.edit_range(start, end)

    def make_iter_blocks (self, *methods):
        """Returns an itertools.cycle object for *methods."""
        return itertools.cycle(methods)

    def match_time (self, string_time, _re=None):
        """
        Check the time-line and return the matched values
        or raise MismatchTimeError.
        A custom regex-pattern object can be used instead
        of the default RE_MATCH_TIME.
        """
        matched = re.match(_re or self.RE_MATCH_TIME, string_time)
        if matched is None:
            raise MismatchTimeError(
                "'{}' (in {})".format(string_time, "match_time"))
        return matched

    def new_sub_num (self, num_str):
        """
        Check the subtitle's number and return it
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

    def new_time (self, hour, min_, sec, ms):
        """
        Returns the new time (in seconds) according to the delta.
        """
        return sum(((hour + self.delta_hour) * self.MAX_H,
                    (min_ + self.delta_min) * self.MAX_MIN,
                    sec + self.delta_sec,
                    ((ms + self.delta_ms) / self.MAX_MS)
                   )) * self.delta_framerate

    def parse (self, lines, itertools_cycle_iterator):
        """Iterate over subtitle's *lines*, using
        *itertools_cycle_iterator* for get the right function
        to manipulate the given line.
        """
        get_func = GetFunc(itertools_cycle_iterator)
        for line, self.actual_numline in zip(lines, itertools.count(1)):
            yield self.output_line_fmt.format(get_func(line))

    def times_from_secs (self, seconds):
        """
        Returns a tuple of (hour, minutes, secs, ms)
        from a time expressed in seconds.
        """
        hour, _ = divmod(seconds, self.MAX_H)
        m, _ = divmod(_, self.MAX_MIN)
        ms, s = math.modf(_)
        return hour, m, s, round(ms*self.MAX_MS)


class MicroDVD (Subtitle):
    """
    Class to manage MicroDVD (*.sub) subtitle.
    """
    def __init__ (self, file_in, file_out, frames=25,
                  unsafe_time_mode=False, use_secs=False):
        """file_in and file_out must be file-like objects."""
        str_fmt = '{{{start:.0f}}}{{{end:.0f}}}{rest}\n'
        reg = '^{(\d+)}{(\d+)}(.*)$'
        reg_unsafe = '^{(-{0,1}\d+)}{(-{0,1}\d+)}(.*)$'
        super().__init__(str_fmt, reg if not unsafe_time_mode else reg_unsafe, str_fmt)
        self.frames = frames
        self.delta_frames = 0
        self.infile = file_in
        self.outfile = file_out
        self._use_sec = use_secs

    def frame_use_secs(self, frame):
        secs, r = divmod(frame, self.frames)
        return r + (sum((self.delta_hour * self.MAX_H,
                            self.delta_min * self.MAX_MIN,
                            secs + self.delta_sec,
                            self.delta_ms))
                       * self.frames
                       * self.delta_framerate)

    def _new_time(self, frames):
        return list(self.frame_use_secs(f) for f in frames)

    def _new_frames(self, frames):
        return [(x + self.delta_frames) * self.delta_framerate for x in frames]

    new_time = _new_frames

    def set_delta (self, hour=0, min_=0, sec=0, ms=0, delta_frames=0):
        """Set time's attribute."""
        super(MicroDVD, self).set_delta(hour, min_, sec, ms, 0)
        self.delta_frames = delta_frames

    def main(self):
        """Do the job."""
        if self._use_sec:
            self.new_time = self._new_time
        for self.actual_numline, line in zip(itertools.count(1), self.infile):
            *time, rest = self.match_time(line).groups()
            if self.check_range_to_edit(int(time[0])):
                start, end = self.new_time(map(int, time))
                self.outfile.write(self.output_line_fmt.format(
                    start=start+self.stretch_left,
                    end=end+self.stretch_right,
                    rest=rest))
            else:
                self.outfile.write(line)

class AssSub (Subtitle):
    """
    Class to manage (Advanced) SubStation Alpha (*.ass/*.ssa) subtitle.
    Inherit from Subtitle.
    """
    def __init__ (self, file_in, file_out, unsafe_time_mode=False):
        """`file_in' and `file_out' must be file-like objects."""
        reg = '(^Dialogue: \d+),(\d{1}:\d{2}:\d{2}([:\.])\d{2}),'\
              '(\d{1}:\d{2}:\d{2}([:.])\d{2}),(.*$)'
        reg_unsafe = '(^Dialogue: \d+),(-{0,1}\d+:\d{2}:\d{2}([:\.])\d{2}),'\
                     '(-{0,1}\d+:\d{2}:\d{2}([:.])\d{2}),(.*$)'
        time_reg = '(\d{1}):(\d{2}):(\d{2})[:\.](\d{2})'
        time_reg_unsafe = '(-{0,1}\d+):(\d{2}):(\d{2})[:\.](\d{2})'
        # Why these regex? well...
        # The spec for ass/ssa file talk about a time format like
        # 0:00:00:00  (so, *1* digit for hours and the colon as divider)
        # ie. Hrs:Mins:Secs:hundredths
        # BUT... some ass/ssa file use dot between Secs and hundredths,
        # and seems that many player accept these; so, we want to
        # preserve the original separator.
        self.reg = (re.compile(reg) if not unsafe_time_mode
                    else re.compile(reg_unsafe))
        self.time_reg = (re.compile(time_reg) if not unsafe_time_mode
                                        else re.compile(time_reg_unsafe))
        super().__init__()
        self.file_in = file_in
        self.file_out = file_out
        self.actual_numline = 0
        self.MAX_MS = self.MAX_HNDRS
        # NOTE: since ass/ssa use 2-digit precision for fraction of seconds
        # *MAX_MS* is used as an alias for *MAX_HNDRS* and *self.delta_ms*
        # used in various methods of the base class refer to hundreds, not
        # milliseconds (to avoid rewrite methods in the base class).

    def _is_in_range (self, time_string):
        """Return a string representing the subtitle time."""
        h, m, s, hndrs = list(map(
            int, self.time_reg.match(time_string).groups()))
        return self.check_range_to_edit(h * self.MAX_H + m * self.MAX_MIN + s)

    def new_time_string (self, time_string, sec_sep, stretch):
        """Return a string representing the subtitle time."""
        h, m, s, hndrs = list(map(
            int, self.time_reg.match(time_string).groups()))
        return '{:.0f}:{:02.0f}:{:02.0f}{sep}{:02.0f}'.format(
            *self.times_from_secs(self.new_time(h, m, s, hndrs + stretch)),
             sep=sec_sep)

    def parse_line (self, line):
        """
        Parse a SubStation Alpha subtitle's line. Fields are:
          Marked, Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
        we care about fields 1 and 2.
        """
        line = line.rstrip()
        if line.startswith('Dialogue:'):
            try:
                match = self.reg.match(line)
                init, start, start_sep, end, end_sep, rest = match.groups()
                if self._is_in_range(start):
                    new_start = self.new_time_string(
                        start, start_sep, self.stretch_left)
                    new_end = self.new_time_string(
                        end, end_sep, self.stretch_right)
                    line = ','.join((init, new_start, new_end, rest))
            except ValueError as err:
                raise MismatchTimeError(
                    "({}) Something went wrong computing this line: {}".format(
                        err, line))
            except AttributeError as err:
                raise MismatchTimeError(
                    ("You probably need to --back-to-the-future"
                     "ERR LINE IS: {}").format(line))
        return line

    def set_delta (self, hour=0, min_=0, sec=0, hndrs=0, *not_used):
        super(AssSub, self).set_delta(hour, min_, sec)
        self.delta_ms = hndrs

    def main (self):
        for self.actual_numline, line in zip(
            itertools.count(1), self.file_in):
            self.file_out.write(self.output_line_fmt.format(self.parse_line(line)))


class SrtSub (Subtitle):
    """
    Class to manage SubRip (*.srt) subtitle.
    Inherit from Subtitle.
    """
    def __init__ (self, file_in, file_out, unsafe_time_mode=False,
                  unsafe_number_mode=False, ignore_extra=False,
                  make_progressive_num_block=False, start_sub_num=1,
                  keep_pos=False):
        """*file_in* and *file_out* must be file-like objects.
        *ignore_extra* is ignored :-D when *keep_pos* is True."""
        self.sub_num = start_sub_num
        self.time_sep = " --> "
        self.string_format = "{:02d}:{:02d}:{:02d},{:03d}"  ###XXX+TODO -d
        reg_safe =   r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$'
        reg_unsafe = r'^(-{0,1}\d{1,}):(\d{2}):(\d{2}),(\d{3})$'
        _s = slice(None, -1) if ignore_extra else slice(None, None)
        self.re_pattern = (reg_unsafe if unsafe_time_mode else reg_safe)[_s]
        self.unsafe_number_mode = unsafe_number_mode
        super().__init__(self.string_format, self.re_pattern)
        self.end_t_reg = (self.RE_MATCH_TIME if not keep_pos
                          else re.compile(
                          r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})(?=\s|$)(.*)?$'))
        self._keep_pos_group = (1,2,3,4,5) if keep_pos else (1,2,3,4)
        self.file_in = file_in
        self.file_out = file_out
        self._sl = self._ml = self._sr = self._mr = 0 # stretch
        if make_progressive_num_block:
            self.new_sub_num = self.progressive_num_block

    @property
    def stretch (self):
        return self.stretch_left, self.stretch_right
    @stretch.setter
    def stretch (self, pair):
        self.stretch_left, self.stretch_right = pair
        if abs(self.stretch_left) >= self.MAX_MS:
            self._sl, self._ml = divmod(abs(self.stretch_left), self.MAX_MS)
            if self.stretch_left < 0:
                self._sl = -self._sl
                self._ml = -self._ml
        else:
            self._ml = self.stretch_left
        if abs(self.stretch_right) >= self.MAX_MS:
            self._sr, self._mr = divmod(abs(self.stretch_right), self.MAX_MS)
            if self.stretch_right < 0:
                self._sr = -self._sr 
                self._mr = -self._mr 
        else:
            self._mr = self.stretch_right

    @iterdec()
    def num_block (self, num_string):
        """Check the subtitle's number identifier lines."""
        self.IS_BLOCK = True
        return self.new_sub_num(num_string)

    def progressive_num_block (self, __ignored_num_str):
        matched = re.match(self.RE_MATCH_NUMBER, __ignored_num_str.rstrip())
        if matched is None and not self.unsafe_number_mode:
            raise IndexNumError(
                "{} ({})".format(__ignored_num_str, self.sub_num))
        else:
            n = self.sub_num
        self.sub_num += 1
        return n

    @iterdec()
    def time_block (self, time_string):
        """Check the time lines."""
        if not self.IN_RANGE:
            return time_string.rstrip()
        try:
            start, end = list(
                map(str.strip, time_string.split(self.time_sep)))
        except ValueError:
            raise MismatchTimeError("[at line {}] '{}' (in {})".format(
                 self.actual_numline, time_string, "time_block"))
        h, m, s, ms = list(map(int, self.match_time(start).group(1, 2, 3, 4)))
        new_start = self.string_format.format(*map(int, self.times_from_secs(
            self.new_time(h, m, s+self._sl, ms+self._ml))))
        h, m, s, ms, *extra = self.match_time(
            end, self.end_t_reg).group(*self._keep_pos_group)
        h, m, s, ms = list(map(int, (h, m, s, ms)))
        extra = extra[0] if extra else ''
        new_end = self.string_format.format(*map(int, self.times_from_secs(
            self.new_time(h, m, s+self._sr, ms+self._mr))))
        return self.time_sep.join((new_start, new_end)) + extra

    @iterdec(multicall=True)
    def text_block (self, line):
        """Returns the text line rstripped (no checks needed)."""
        self.IS_BLOCK = False
        return line.rstrip()

    def main (self):
        """Doing the job. """       
        cycle = self.make_iter_blocks(self.num_block,
                                      self.time_block,
                                      self.text_block)
        self.file_out.writelines(self.parse(self.file_in, cycle))
        if self.IS_BLOCK and self.IS_WARN:
            warnings.warn("Incomplete block at EOF", IncompleteBlockError)


###########
# M A I N #
###########

if __name__ == '__main__':
    parser = get_parser()
    opts = parser.parse_args()
    opt_err = Template("Can't use $what with $subtype subtitles\n")
    opt_err_pairs = (
        [opts.ignore_extra, '-I/--ignore-extra'],
        [opts.unsafe_number_mode, '-B/--back-to-the-block'],
        [opts.num, '-n/--num'])
    if opts.info:
        print(__doc__)
        sys.exit(0)
    if opts.same_file:
        if any((opts.infile, opts.outfile)):
            print(('{}: -O/--same-file can not be used in conjunction with '
                  '-i/--input-file or -o/--output-file').format(sys.argv[0]),
                  file=sys.stderr)
            sys.exit(1)
        else:
            opts.infile = opts.outfile = opts.same_file
    if opts.subtitle_type == 'srt':
        if ((opts.prog_sub_num is not None)
            and (opts.num or (opts.range != OPT_RANGE))):
            co = ('-r/--range', '-n/--number')[bool(opts.num)]
            print('{}: option -N/--make-progressive-num-blocks'
                  ' conflicts with {}'.format(
                      sys.argv[0], co), file=sys.stderr)
            sys.exit(1)
    try:
        codecs.lookup(opts.encoding.lower())
    except LookupError as le:
        print('{prog}: {err}'.format(prog=sys.argv[0], err=le),
              file=sys.stderr)
        sys.exit(1)
    if not (os.path.exists(opts.tempdir) and os.path.isdir(opts.tempdir)):
        parser.error("tempdir must be an existing directory!")
    else:
        tempfile.tempdir = opts.tempdir
    if not opts.subtitle_type:
        parser.error("subtitle type (-t/--type) must be specified!")
    if opts.infile and not os.path.isfile(opts.infile):
        parser.error("invalid input file '{}'".format(opts.infile))
    if opts.subtitle_type != 'srt':
        for o, s in opt_err_pairs:
            if o:
                parser.error(
                    opt_err.substitute(
                        subtype=opts.subtitle_type, what=s))
    in_file = sys.stdin
    out_file = sys.stdout
    if opts.infile == opts.outfile and all((opts.infile, opts.outfile)):
        tmpfile = TempFile(opts.infile)
        atexit.register(clean_backup, tmpfile)
        in_file = open(tmpfile.filepath, 'r',
                       encoding=opts.encoding, errors=opts.enc_err)
        out_file = open(opts.infile, 'w',
                        encoding=opts.encoding, errors=opts.enc_err)
    else:
        tmpfile = TempFile(None)
        atexit.register(clean_backup, tmpfile)
        if opts.infile:
            in_file = open(opts.infile, "r",
                           encoding=opts.encoding, errors=opts.enc_err)
        if opts.outfile:
            out_file = open(opts.outfile, "w",
                            encoding=opts.encoding, errors=opts.enc_err)
    if opts.subtitle_type == 'srt':
        newsub = SrtSub(in_file, out_file, opts.unsafe_time_mode,
                        opts.unsafe_number_mode, opts.ignore_extra,
                        opts.prog_sub_num != None,
                        opts.prog_sub_num, opts.preserve_extra)
        newsub.set_delta(opts.hour, opts.min, opts.sec, opts.ms, opts.num)
    elif opts.subtitle_type in ('sub', 'microdvd'):
        use_secs = any((opts.hour, opts.min, opts.sec, opts.ms))
        newsub = MicroDVD(in_file, out_file, opts.frames,
                          opts.unsafe_time_mode, use_secs)
        if opts.delta_frames and use_secs:
            save_on_error(in_file, out_file, tmpfile)
            parser.error("You can't use frames and time delta together")
        newsub.set_delta(opts.hour, opts.min, opts.sec,
                         opts.ms, opts.delta_frames)
    elif opts.subtitle_type in ('ass', 'ssa'):
        newsub = AssSub(in_file, out_file, opts.unsafe_time_mode)
        newsub.set_delta(opts.hour, opts.min, opts.sec, opts.ms, opts.num)
    newsub.IS_WARN = opts.is_warn
    if opts.skip_bytes:
        if opts.skip_bytes < 0:
            save_on_error(in_file, out_file, tmpfile)
            parser.error('-s|--skip-byte argument must be a positive value')
        try:
            skip_bytes(in_file, opts.skip_bytes)
        except Exception as e:
            save_on_error(in_file, out_file, tmpfile)
            print("{err}: [skip_bytes] {msg}\n".format(
                    err=e.__class__.__name__, msg=str(e)), file=sys.stderr)
            sys.exit(1)
    try:
        start_sub, end_sub = opts.range.split(':')
        newsub.set_subs_range(int(start_sub) if start_sub else None,
                              int(end_sub) if end_sub else None)
    except Exception as e:
        save_on_error(in_file, out_file, tmpfile)
        parser.error('invalid -r/--range option: {val} [{err}]'.format(
            val=opts.range, err=str(e)))
    if opts.stretch:
        try:
            sl, sr = get_stretch(opts.stretch)
            newsub.stretch = sl, sr
        except Exception as e:
            save_on_error(in_file, out_file, tmpfile)
            parser.error('invalid --stretch option: {val} [{err}]'.format(
                val=opts.stretch, err=str(e)))
    if opts.change_framerate:
        newsub.change_framerate(*opts.change_framerate)
    try:
        newsub.main()
    except (BadFormatError, MismatchTimeError,
            IndexNumError, UnicodeDecodeError) as e:
        print("{err}: [at line {line}] {msg}\n".format(
            err=e.__class__.__name__, line=newsub.actual_numline, msg=str(e)),
              file=sys.stderr)
        save_on_error(in_file, out_file, tmpfile)
        sys.exit(1)
    except KeyboardInterrupt:
        print('csub: User Interrupt')
        save_on_error(in_file, out_file, tmpfile)
        sys.exit(1)
    except Exception as e:
        ue_msg = "Unknow error! surely a bug. Shit!\n[at line {line}] {msg}\n"
        print(ue_msg.format(line=newsub.actual_numline, msg=str(e)),
              file=sys.stderr)
        save_on_error(in_file, out_file, tmpfile)
        sys.exit(255)
    else:
        close_files((in_file, out_file))
