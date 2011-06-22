#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test suite for csub

"""

import re
import sys
import os
import os.path as op
import glob
import copy
import random
import inspect
import unittest
import io
import itertools
import subprocess as sbp
import shlex
import operator
import platform
import tempfile


PYTHON_EXE = 'python3'
PROGFILE = 'csub.py'
DATA_DIR = 'data'
CWD = op.dirname(op.realpath(__file__))


class TempFileTest (unittest.TestCase):

    def testTempFileObjects (self):
        tmp_1 = csub.TempFile(None)
        tmp_2 = csub.TempFile(sys.stdin)
        tmp_others = [csub.TempFile(f)
                      for f in glob.glob(op.join(CWD, DATA_DIR, '*.srt'))]
        self.assertTrue(hasattr(tmp_1, '_fake'))
        self.assertTrue(hasattr(tmp_2, '_fake'))
        for tmpf in tmp_others:
            self.assertFalse(hasattr(tmpf, '_fake'))
        tmp_3 = tmp_others[0]
        for method in ('close', 'read', 'seek', 'write_back'):
            m1 = inspect.getsourcelines(getattr(tmp_1, method))
            m2 = inspect.getsourcelines(getattr(tmp_2, method))
            m3 = inspect.getsourcelines(getattr(tmp_3, method))
            self.assertEqual(m1, m2, "Not the same method!")
            self.assertEqual(m1, m2, "Not the same method!")
            self.assertNotEqual(m1, m3, "Are the same method!")
            self.assertNotEqual(m2, m3, "Are the same method!")

    def testTempSafety (self):
        # input and output in the same file:
        testsub = op.join(CWD, DATA_DIR, 'fail_sub_1.srt')
        with open(testsub, 'r') as ts:
            string_sub = ts.read()
        tmpfile = csub.TempFile(testsub)
        with open(tmpfile.filepath, 'r') as in_file:
            with open(testsub, 'w') as out_file:
                newsub = csub.SrtSub(in_file, out_file)
                self.assertRaises(csub.MismatchTimeError, newsub.main)
        tmpfile.write_back()
        with open(testsub, 'r') as ts:
            self.assertEqual(ts.read(), string_sub,
                             "sub file shouldn't be modified!")
        # unsafe mode, no error should be raised:
        with open(testsub, 'r') as ts:
            outfile = csub.TempFile(testsub)
            with open(outfile.filepath, 'w') as out:
                newsub = csub.SrtSub(ts, out, True)
                newsub.main()

    def testCmdlineOnFailSrt (self):
        commands = ["{exe} {prog} -i {input} -o {output}",
                    "{exe} {prog} -i __FAIL__{input} -o {output} -t ass",
                    "{exe} {prog} -i {input} -o {output} -t srt -H foo",
                    "{exe} {prog} -i {input} -o {output} -t srt --not-exist",
                    "{exe} {prog} -i {input} -o {output} -t srt -m 9999",]
        cmd_dict = {'exe':PYTHON_EXE, 'input':None,'output':None, 'prog':PROGFILE}
        for subfile in itertools.chain(
            glob.glob(op.join(CWD, DATA_DIR, 'test*.srt'))):
            with open(subfile) as f:
                orig = f.read()
            for cmd in commands:
                _d = cmd_dict.copy()
                _d['input'] = _d['output'] = subfile
                cmdline = shlex.split(cmd.format(**_d))
                pipe = sbp.Popen(cmdline, stdout=sbp.PIPE, stderr=sbp.PIPE)
                pipe.communicate()[0]
                retcode = pipe.returncode
                self.assertNotEqual(retcode, 0,
                                    "Retcode is %d | %s | %s |"
                                    % (retcode, cmdline, subfile))
                with open(subfile) as f:
                    self.assertEqual(f.read(), orig,
                                     "sub file shouldn't be modified!")

    def testCmdlineOnFailAss (self):
        commands = ["{exe} {prog} -i {input} -o {output}",
                    "{exe} {prog} -i {input} -o {output} -t srt",
                    "{exe} {prog} -i {input} -o {output} -t sub -r 1:2",
                    "{exe} {prog} -i {input} -o {output} -t ass -n 11",
                    "{exe} {prog} -i {input} -o {output} -t ass -B",]
        cmd_dict = {'exe':PYTHON_EXE, 'input':None,'output':None, 'prog':PROGFILE}
        for subfile in itertools.chain(
            glob.glob(op.join(CWD, DATA_DIR, 'test*.sub'))):
            with open(subfile) as f:
                orig = f.read()
            for cmd in commands:
                _d = cmd_dict.copy()
                _d['input'] = _d['output'] = subfile
                cmdline = shlex.split(cmd.format(**_d))
                pipe = sbp.Popen(cmdline, stdout=sbp.PIPE, stderr=sbp.PIPE)
                pipe.communicate()[0]
                retcode = pipe.returncode
                self.assertNotEqual(retcode, 0,
                                    "Retcode is %d | %s | %s |"
                                    % (retcode, cmdline, subfile))
                with open(subfile) as f:
                    self.assertEqual(f.read(), orig,
                                     "sub file shouldn't be modified!")

    def testCmdlineOnFailMicroDVD (self):
        commands = ["{exe} {prog} -i {input} -o {output}",
                    "{exe} {prog} -i {input} -o {output} -t srt",
                    "{exe} {prog} -i {input} -o {output} -t sub -f foo",
                    "{exe} {prog} -i {input} -o {output} -t sub -F",
                    "{exe} {prog} -i {input} -o {output} -t sub -f",
                    "{exe} {prog} -i {input} -o {output} -t sub -r 1:2",
                    "{exe} {prog} -i {input} -o {output} -t sub -n 11",
                    "{exe} {prog} -i {input} -o {output} -t sub -B",]
        cmd_dict = {'exe':PYTHON_EXE, 'input':None,'output':None, 'prog':PROGFILE}
        for subfile in itertools.chain(
            glob.glob(op.join(CWD, DATA_DIR, 'test*.ass'))):
            with open(subfile) as f:
                orig = f.read()
            for cmd in commands:
                _d = cmd_dict.copy()
                _d['input'] = _d['output'] = subfile
                cmdline = shlex.split(cmd.format(**_d))
                pipe = sbp.Popen(cmdline, stdout=sbp.PIPE, stderr=sbp.PIPE)
                pipe.communicate()[0]
                retcode = pipe.returncode
                self.assertNotEqual(retcode, 0,
                                    "Retcode is %d | %s | %s |"
                                    % (retcode, cmdline, subfile))
                with open(subfile) as f:
                    self.assertEqual(f.read(), orig,
                                     "sub file shouldn't be modified!")

class MicroDVDFIleTest (unittest.TestCase):
    """Test operation on microDVD files. """
    def testOkMicroDvdSub (self):
        for sub in (MICRODVD_FAKESUB_0,
                    MICRODVD_FAKESUB_1,
                    MICRODVD_FAKESUB_2,):
            infile = io.StringIO(sub)
            outfile = io.StringIO()
            #in_file, out_file, opts.frames, opts.unsafe_time_mode, use_secs
            inst = csub.MicroDVD(infile, outfile)
            inst.main()
            infile.seek(0)
            outfile.seek(0)
            self.assertEqual(infile.read(), outfile.read())

    def testMicroDvdTimeTransformFrames (self):
        _r = random.randint
        for sub in (MICRODVD_FAKESUB_0,
                    MICRODVD_FAKESUB_1,
                    MICRODVD_FAKESUB_2,):
            for i in range(1000):
                frame_delta = _r(1, 10000)
                infile = io.StringIO(sub)
                outfile = io.StringIO()
                #in_file, out_file, opts.frames, opts.unsafe_time_mode, use_secs
                inst = csub.MicroDVD(infile, outfile)
                #opts.hour, opts.min, opts.sec, opts.ms, opts.delta_frames
                inst.set_delta(0,0,0,0, frame_delta)
                inst.main()
                infile.seek(0)
                outfile.seek(0)
                self.assertNotEqual(infile.read(), outfile.read())
                # revert
                outfile.seek(0)
                outfile2 = io.StringIO()
                inst = csub.MicroDVD(outfile, outfile2)
                inst.set_delta(0,0,0,0, -frame_delta)
                inst.main()
                infile.seek(0)
                outfile2.seek(0)
                self.assertEqual(infile.read(), outfile2.read())

    def testMicroDvdTimeTransformSecs (self):
        _r = random.randint
        for sub in (MICRODVD_FAKESUB_0,
                    MICRODVD_FAKESUB_1,
                    MICRODVD_FAKESUB_2,):
            for i in range(1000):
                infile = io.StringIO(sub)
                outfile = io.StringIO()
                #in_file, out_file, opts.frames, opts.unsafe_time_mode, use_secs
                inst = csub.MicroDVD(infile, outfile, use_secs=True)
                #opts.hour, opts.min, opts.sec, opts.ms, opts.delta_frames
                inst_args = [_r(1,10), _r(1,100), _r(1, 200), _r(100,3300), 0]
                inst.set_delta(*inst_args)
                inst.main()
                infile.seek(0)
                outfile.seek(0)
                self.assertNotEqual(infile.read(), outfile.read())
                # revert
                infile.seek(0)
                outfile.seek(0)
                outfile2 = io.StringIO()
                inst = csub.MicroDVD(outfile, outfile2, use_secs=True)
                inst_args = list(-x for x in inst_args)
                inst.set_delta(*inst_args)
                inst.main()
                outfile2.seek(0)
                self.assertEqual(infile.read(), outfile2.read())

    def testMicroDvdTimeFail (self):
        fail_subs = (MICRODVD_FAKESUB_FAIL_SYNTAX_6,
                    MICRODVD_FAKESUB_FAIL_SYNTAX_7,)
        for sub in fail_subs:
            infile = io.StringIO(sub)
            outfile = io.StringIO()
            inst = csub.MicroDVD(infile, outfile)
            self.assertRaises(csub.MismatchTimeError, inst.main)
        # fail without --back-to-the-future
        fail_b_subs = (MICRODVD_FAKESUB_FAIL_TIME_IF_NOT_B_3,
                       MICRODVD_FAKESUB_FAIL_TIME_IF_NOT_B_4,
                       MICRODVD_FAKESUB_FAIL_TIME_IF_NOT_B_5,)
        for sub in fail_b_subs:
            # error:
            infile = io.StringIO(sub)
            outfile = io.StringIO()
            inst = csub.MicroDVD(infile, outfile)
            self.assertRaises(csub.MismatchTimeError, inst.main)
            # ok:
            infile.seek(0)
            outfile.seek(0)
            inst = csub.MicroDVD(infile, outfile, unsafe_time_mode=True)
            inst.set_delta(1,1,1,1,1)
            inst.main()
            infile.seek(0)
            outfile.seek(0)
            self.assertNotEqual(infile.read(), outfile.read())
            
                                
class SrtFileTest (unittest.TestCase):
    """Test operation on files. """

    def testOkSrtSub (self):
        if platform.system() == 'Windows':
            self.skipTest('actually not available on Windows platform')
        options = ["-H", "-M", "-S", "-m", "-n"]
        lenopt = len(options)
        cmdline = [PYTHON_EXE, PROGFILE]
        for sub in (SRT_FAKESUB_0, SRT_FAKESUB_1, SRT_FAKESUB_2):
            choosed = cmdline[:]
            back_to = cmdline[:]
            opts = options[:]
            random.shuffle(opts)
            for n in range(random.randint(1, lenopt)):
                o, v = opts.pop(), random.randint(0, 999)
                back_to.append("%s %d" % (o, -v))
                choosed.append("%s %d" % (o, v))
            cmdline.append('%s srt' %
                           ('-t' if random.randint(0,1) else '--type'))
            cmdline = shlex.split(' '.join(cmdline))
            fpipe = sbp.Popen(["echo", "-n", sub], shell=True, stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, shell=True,
                              stdin=fpipe.stdout, stdout=sbp.PIPE)
            fpipe.stdout.close() 
            new_text = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0,
                             "Retcode is %d %s %s" % (retcode, cmdline, sub))
            fpipe = sbp.Popen(["echo", "-n", new_text],
                              shell=True, stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, shell=True,
                              stdin=fpipe.stdout,
                              stdout=sbp.PIPE)
            fpipe.stdout.close() 
            spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, "Retcode is %d" %retcode)

    def testFailSrtSubs (self):
        if platform.system() == 'Windows':
            self.skipTest('actually not available on Windows platform')
        fail_list = [SRT_FAKESUB_6_FAIL_INDEX, SRT_FAKESUB_7_FAIL_INDEX,
                     SRT_FAKESUB_8_FAIL_INDEX,SRT_FAKESUB_9_FAIL_INDEX, 
                     SRT_FAKESUB_3_FAIL_TIME, SRT_FAKESUB_4_FAIL_TIME, 
                     SRT_FAKESUB_5_FAIL_TIME, SRT_FAKESUB_6_FAIL_TIME,]
        cmdline = [PYTHON_EXE, PROGFILE]
        cmdline.append('%s srt' %
                       ('-t' if random.randint(0,1) else '--type'))
        cmdline = shlex.split(' '.join(cmdline))
        for sub in fail_list:
            fpipe = sbp.Popen(["echo", "-n"], shell=True, stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, shell=True,
                              stdin=fpipe.stdout, stdout=sbp.PIPE)
            fpipe.stdout.close()
            out = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, (retcode))

    def testSrtIndex (self):
        for sub_string in (SRT_FAKESUB_6_FAIL_INDEX,
                           SRT_FAKESUB_7_FAIL_INDEX,
                           SRT_FAKESUB_8_FAIL_INDEX, 
                           SRT_FAKESUB_9_FAIL_INDEX,):
            sub = io.StringIO(sub_string)
            newsub = csub.SrtSub(sub, copy.deepcopy(sub))
            self.assertRaises(csub.IndexNumError, newsub.main)

    def testUnhandledError (self):
        def  get_error (error):
            def raise_error (*args):
                raise error
            return raise_error
        errors = [TypeError, UnboundLocalError, ValueError,
                  IOError, OSError, SystemError, AttributeError,]
        for error in errors:
            sub = io.StringIO(SRT_FAKESUB_0)
            newsub = csub.SrtSub(sub, sub)
            newsub.match_time = get_error(error)
            try:
                newsub.main()
            except Exception as e:
                msg = "it should be %s" % e
                self.assertNotEqual(e, csub.MismatchTimeError, msg)
                self.assertNotEqual(e, csub.IndexNumError, msg)


class SrtReTest (unittest.TestCase):

    def setUp (self):
        self.subs = csub.SrtSub(None, None)
        self.time_string_ok = ("00:12:56,123", "01:56:00,000", "12:00:02,999",
                               "00:10:12,010", "00:44:44,123",)
        self.time_string_ok__unsafe = "-1:44:44,123"
        self.time_string_err = ("0:44:44,123", "-1:44:44,123",
                                "1:44:44,123", "01:56:1,123",
                                "01:56:00,00", "01:56:00,1",
                                "02:-4:44,123", "00:44:-44,123",
                                "00:44:44,-123", "+00:44:44,123",
                                "00:+44:44,123", "00:44:+44,123",
                                "00:44:44,+123", "01:4:+19,123",
                                "00:44:33:123", "OO:44:33,123",
                                "00:44:33,0xa", "00:4a:33,123",
                                "01:56:111,234", "01:2:00,343",
                                "01:562:00,432","1:56:00,000",
                                "-11:562:00,432","-1:56:00,000",)
        self.number_string_ok =("1", "01", "0009", "09", "1234567",
                                "-12", "01", "0", "-02", "-93",)
        self.number_string_err =("+097a", "07a",  "0xffffffff", "+", "-",
                                  "-2e10",  "2e10", "stringa",)

    def testSrtReTime (self):
        self.unsafe_subs = csub.SrtSub(None, None, True) # for testing unsafe mode
        for string in self.time_string_ok:
            self.assertTrue(self.subs.match_time(string),
                            "Failed on %s" % string)
            self.assertTrue(self.unsafe_subs.match_time(string),
                            "Failed on %s" % string)
        self.assertTrue(self.unsafe_subs.match_time(self.time_string_ok__unsafe),
                        "Failed on %s" % self.time_string_ok__unsafe)
        for string in self.time_string_err:
            self.assertRaises(csub.MismatchTimeError,
                              self.subs.match_time, string)

    def testSrtReNumber (self):
        for string in self.number_string_ok:
            self.assertTrue((self.subs.new_sub_num(string) is not None),
                            "Failed on %s" % string)
        for string in self.number_string_err:
            self.assertRaises(csub.IndexNumError,
                              self.subs.new_sub_num, string)


class SrtTimeTransformTest (unittest.TestCase):

    def setUp (self):
        self.subs = csub.SrtSub(None, None)
        self.subs.ITER_FUNC = self.subs.make_iter_blocks(
            self.subs.text_block, lambda *args: args)
        self.subs._get_func = next(self.subs.ITER_FUNC)
        self.sep_err = ("00:01:31,970-->00:01:33,450",
                        "00:01:31,970 -> 00:01:33,450",
                        "00:01:31,970  00:01:33,450",)
        self.time_lines = ("00:58:18,860 --> 00:58:21,950",
                           "00:59:00,600 --> 00:59:03,530",
                           "00:59:05,370 --> 00:59:07,470",
                           "00:01:31,970 --> 00:01:33,450",
                           "00:01:35,710 --> 00:01:43,690",
                           "00:01:55,820 --> 00:01:57,870",)
        self.time_strings = ((("00:01:31,970", 1, 0, 0, 0), "01:01:31,970"),
                             (("00:01:33,450", 0, 3, 11, 1), "00:04:44,451"),
                             (("00:01:35,710", 0, 59, 0, 0), "01:00:35,710"),
                             (("00:01:43,690", 0, 0, 20, 0), "00:02:03,690"),
                             (("00:01:55,820", 0, 59, 5, 0), "01:01:00,820"),
                             (("00:01:55,820", 0, 59, 5, 180), "01:01:01,000"),
                             (("00:01:57,870", 0, -1, 3, 0), "00:01:00,870"),
                             (("00:01:57,870", 0, -1, 3, -871), "00:00:59,999"),
                             (("01:58:18,860", 1, -60, 0, 0), "01:58:18,860"),
                             (("01:58:21,950", 1, 0, -3600, 0), "01:58:21,950"),
                             (("00:59:00,600", 0, 0, 0, 400), "00:59:01,000"),
                             (("00:59:03,530", 0, 1, 57, -530), "01:01:00,000"),
                             (("02:00:00,370", -1, 0, 0, -371), "00:59:59,999"), 
                             (("00:59:07,470", 0, -59, -7, -470), "00:00:00,000"),
                             (("01:14:00,600", -1, 60, 0, 0), "01:14:00,600"),
                             (("02:59:03,530", 0, 0, 57, -529), "03:00:00,001"),
                             (("01:59:00,001", 0, 0, 0, -2), "01:58:59,999"),
                             (("02:59:59,060", 0, 0, 0, 940), "03:00:00,000"),)

    def update_time (self, string_time, hours, mins, secs, ms):
        self.subs.set_delta(hours, mins, secs, ms, 0)
        h, m, s, ms = list(map(int, self.subs.match_time(string_time).group(1, 2, 3, 4)))
        secs, ms = self.subs.new_time_tuple(h, m, s, ms)
        nh, nm, ns = self.subs.times_from_secs(secs)
        return self.subs.string_format % (nh, nm, ns, ms)

    def random_time (self, orig_time_string):
        delta_time = [random.randint(-100, 2000) for i in ("h", "m", "s", "n")]
        delta_time.insert(-1, random.randint(-999, 999))
        self.subs.set_delta(*delta_time)
        new_time_string = self.subs.time_block(orig_time_string)[0]
        self.subs.set_delta(*list(map(int.__neg__, delta_time)))
        return self.subs.time_block(new_time_string)[0]

    def testSrtTimeSep (self):
        for string in self.sep_err:
            self.assertRaises(csub.MismatchTimeError,
                              self.subs.time_block, string)

    def testTimeCalc (self):
        self.subs = csub.SrtSub(None, None, True)
        for tlines in self.time_lines:
            self.assertEqual(tlines, self.subs.time_block(tlines)[0],
                             "wrong time update in %s" % repr(tlines))
        for tlines in self.time_lines:
            self.assertEqual(tlines, self.random_time(tlines),
                             "wrong (random) time update in %s" % repr(tlines))
        for strtime in self.time_strings:
            self.assertEqual(self.update_time(*strtime[0]),
                             strtime[1],
                             "failed on %s"  % repr(strtime))


class AssFileTest (unittest.TestCase):
    def testAssTimeTransform (self):
        subtitles = (ASS_FAKESUB_1,ASS_FAKESUB_2_OK_MISC,)
        _neg = operator.neg
        _r = random.randint
        for i in range(200):
            for subtitle in subtitles:
                sub_orig = io.StringIO(subtitle)
                sub_in = io.StringIO(subtitle)
                sub_out = io.StringIO()
                inst = csub.AssSub(sub_in, sub_out)
                time_delta = [_r(1,3), _r(1,200), _r(1,200), _r(1,200)]
                inst.set_delta(*time_delta)
                inst.main()
                sub_in.seek(0)
                sub_out.seek(0)
                self.assertNotEqual(sub_in.read(), sub_out.read())
                sub_in.seek(0)
                sub_out.seek(0)
                sub_in.truncate(0)
                inst = csub.AssSub(sub_out, sub_in)
                inst.set_delta(*list(_neg(t) for t in time_delta))
                inst.main()
                sub_in.seek(0)
                self.assertEqual(sub_in.read(), sub_orig.read())

    def testAssSubsOk (self):
        subtitles = (ASS_FAKESUB_1,ASS_FAKESUB_2_OK_MISC,)
        _neg = operator.neg
        _r = random.randint
        for subfile in glob.glob(op.join(CWD, DATA_DIR, 'test*.ass')):
            with open(subfile, 'r') as infile:
                outfile = io.StringIO()
                inst = csub.AssSub(infile, outfile)
                inst.main()
                infile.seek(0)
                outfile.seek(0)
                self.assertEqual(infile.read(), outfile.read())
        for i in range(200):
            for subtitle in subtitles:
                sub_orig = io.StringIO(subtitle)
                sub_in = io.StringIO(subtitle)
                sub_out = io.StringIO()
                inst = csub.AssSub(sub_in, sub_out)
                time_delta = [_r(11,13), _r(1,200), _r(1,200), _r(1,200)]
                inst.set_delta(*time_delta)
                inst.main()
                # check back, fail without -b option:
                sub_out.seek(0)
                sub_in.seek(0)
                sub_in.truncate()
                inst = csub.AssSub(sub_out, sub_in)
                inst.set_delta(*list(_neg(t) for t in time_delta))
                self.assertRaises(csub.MismatchTimeError, inst.main)
                # no fail:
                sub_out.seek(0)
                sub_in.seek(0)
                sub_in.truncate()
                inst = csub.AssSub(sub_out, sub_in, True)
                inst.set_delta(*list(_neg(t) for t in time_delta))
                sub_in.seek(0)
                inst.main()
                sub_in.seek(0)
                self.assertEqual(sub_in.read(), sub_orig.read())
                
    def testAssFail (self):
        subtitles = (ASS_FAKESUB_3_FAIL_TIME,
                     ASS_FAKESUB_4_FAIL_TIME_H,
                     ASS_FAKESUB_5_FAIL_TIME_H,
                     ASS_FAKESUB_6_FILE_TIME_IF_NOT_B,)
        for subfile in glob.glob(op.join(CWD, DATA_DIR, 'fail*.ass')):
            with open(subfile, 'r') as infile:
                outfile = io.StringIO()
                inst = csub.AssSub(infile, outfile)
                self.assertRaises(csub.MismatchTimeError, inst.main)
        for subtitle in subtitles:
                sub_in = io.StringIO(subtitle)
                sub_out = io.StringIO()
                inst = csub.AssSub(sub_in, sub_out)
                inst.set_delta()
                self.assertRaises(csub.MismatchTimeError, inst.main)
        # no failure if -b option is enabled
        nofail_sub = ASS_FAKESUB_6_FILE_TIME_IF_NOT_B
        sub_in = io.StringIO(nofail_sub)
        sub_out = io.StringIO()
        inst = csub.AssSub(sub_in, sub_out, True)
        inst.set_delta()
        inst.main()
        # and let's check if the output is the same...
        sub_in.seek(0)
        sub_out.seek(0)
        self.assertEqual(sub_in.read(), sub_out.read())        


class MiscTest (unittest.TestCase):
    def testSkip(self):
        _r = random.randint
        for file in glob.glob(op.join(CWD, DATA_DIR, '[a-z]*.srt')):
            for mode in ('r','rb'):
                with open(file, mode=mode) as sub:
                    bytes = _r(0, len(sub.read())-1)
                    sub.seek(0)
                    readed = csub.skip_bytes(sub, bytes)
                    self.assertEqual(len(readed), bytes)
                    sub.seek(0)
                    self.assertEqual(readed, sub.read(bytes))

    def testGoodEncoding(self):
        files = glob.glob(op.join(CWD, DATA_DIR, '_enc_*.srt'))
        for file in files:
            enc = re.match('_enc_([-\w]+)\..*$', op.basename(file)).group(1)
            with open(file, encoding=enc) as fin:
                with tempfile.NamedTemporaryFile() as _fout:
                    _out = _fout.name
                with open(_out, mode='w', encoding=enc) as fout:
                    inst = csub.SrtSub(fin, fout)
                    inst.main()
            with open(file, 'rb') as fin_t:
                with open(_out, 'rb') as fout_t:
                    self.assertEqual(fin_t.read(), fout_t.read())

    def testFailEncoding(self):
       _f = ['_enc_ISO-8859-15.srt', '_enc_utf-8.srt']
       files = [op.join(CWD, DATA_DIR, f) for f in _f]
       enc = 'us-ascii'
       for file in files:
           with open(file, encoding=enc) as fin:
               with tempfile.NamedTemporaryFile() as _fout:
                   _out = _fout.name
               with open(_out, mode='w', encoding=enc) as fout:
                   inst = csub.SrtSub(fin, fout)
                   self.assertRaises(UnicodeDecodeError, inst.main)
                   
    def testLookupEncoding(self):
        fake_encs = ['us-asciiuga', 'utf-otto', 'foo-far-baz']
        files = glob.glob(op.join(CWD, DATA_DIR, '_enc_*.srt'))
        cmdline = "{exe} {prog} -i {fin} -o {fout} -t srt -e {enc}"
        cmd_dict = {'exe':PYTHON_EXE, 'prog':PROGFILE, 'enc':None,}
        for file in files:
            enc = re.match('_enc_([-\w]+)\..*$', op.basename(file)).group(1)
            cmd_dict['enc'] = enc
            cmd_dict['fin'] = file
            with tempfile.NamedTemporaryFile() as fout:
                cmd_dict['fout'] = fout.name
            cmd = shlex.split(cmdline.format(**cmd_dict))
            pipe = sbp.Popen(cmd, stdout=sbp.PIPE, stderr=sbp.PIPE)
            pipe.communicate()
            self.assertEqual(pipe.returncode, 0)
        for enc in fake_encs:
            cmd_dict['enc'] = enc
            cmd = shlex.split(cmdline.format(**cmd_dict))
            pipe = sbp.Popen(cmd, stdout=sbp.PIPE, stderr=sbp.PIPE)
            pipe.communicate()
            self.assertNotEqual(pipe.returncode, 0)



def load_tests():
    loader = unittest.TestLoader()
    test_cases = (SrtFileTest, SrtReTest, SrtTimeTransformTest,
                  TempFileTest, AssFileTest, MicroDVDFIleTest,
                  MiscTest)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    progdir = op.split(op.dirname(op.realpath(__file__)))[0]
    datadir = op.join(progdir, DATA_DIR)
    sys.path.insert(0, progdir)
    sys.path.insert(0, datadir)
    import csub
    from data.sub_strings import *
    PROGFILE = op.join(op.split(op.dirname(op.realpath(__file__)))[0], 'csub.py')
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
    for f in glob.glob("%s.py[oc]" % op.splitext(PROGFILE)[0]):
        os.remove(f) 

