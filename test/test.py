#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test suite for csub

"""

import re
import sys
import os
import os.path as op
import glob
import random
import inspect
import unittest
import StringIO
import subprocess as sbp


PROGFILE = 'csub.py'


FAKESUB_0 = """1567
01:26:32,200 --> 01:26:35,060
"un figlio di puttana faceva ruotare la freccetta
e mi prendeva a calci in culo, Eddie.

1568
01:26:35,830 --> 01:26:38,430
"Poi dovevo andare a scuola e vedere
gli altri bambini mangiare cibo vero.

1569
01:26:38,500 --> 01:26:41,310
"Dovevo vederli mangiare burro d'arachidi
gelatina, carne, pasta,

1570
01:26:41,380 --> 01:26:44,140
"prosciutto e formaggio.
Io avevo un dannato sandwich di Pongo.

1571
01:26:45,730 --> 01:26:48,050
"Poi, per dessert, tiravano fuori
una merendina

1572
01:26:48,190 --> 01:26:50,180
"Ed io dovevo mangiarmi una dannata Slinky?
"""

FAKESUB_1 = """242
00:12:34,439 --> 00:12:38,565
Beh, prima di tutto il Nuovo Testamento venne
dopo l'Antico Testamento, siamo d'accordo?

243
00:12:38,600 --> 00:12:40,231
Certo, ma non significa nulla.

244
00:12:40,266 --> 00:12:44,085
Significa che chi scrisse il Nuovo Testamento
aveva letto prima l'Antico Testamento,

245
00:12:44,120 --> 00:12:45,874
e ha fatto avverare le profezie.

246
00:12:45,909 --> 00:12:47,568
Non puoi far avverare
qualcosa che non e' successo.

247
00:12:47,603 --> 00:12:48,643
Certo che si'.

248
00:12:48,678 --> 00:12:51,615
Sta dicendo che la Bibbia
e' un documento fittizio?
"""

FAKESUB_2 = """7
00:17:11,480 --> 00:17:13,640
I'm pit boss here on Level 2.

8
00:17:14,920 --> 00:17:16,280
Deep-fried robot!

9
00:17:16,480 --> 00:17:19,520
-Just tell me why
-Read this 55-page warrant

10
00:17:19,720 --> 00:17:23,480
-There must be robots worse than I
-There really aren 't

11
00:17:23,680 --> 00:17:27,480
Please let me explain
My crimes were merely boyish pranks
"""

FAKESUB_3_FAIL_TIME = """170
00:11:21,220 --> 00:11:23,897
Sono perfettamente a mio agio
con i fluidi corporei...

171

sangue, muco, lacrime...
"""

FAKESUB_4_FAIL_TIME = """172
00:11:26,316 --> 00:11:28,965
ma con le emozioni che
li accompagnano...

173
non ci so fare altrettanto bene.

00:11:32,015 --> 00:11:33,031
Dexter...
"""

FAKESUB_5_FAIL_TIME = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.

183

00:12:00,449 --> 00:12:01,997
- Sempre.
- Non...

184
00:12:03,515 --> 00:12:04,750
sempre sempre.
"""

FAKESUB_6_FAIL_TIME = """172
00:11:26,316 --> 00:11:28,965
ma con le emozioni che
li accompagnano...

173
non ci so fare altrettanto bene.

00:11:32,015 --> 00:11:33,031
Dexter...
"""

FAKESUB_6_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.

error here!

00:12:00,449 --> 00:12:01,997
"""

FAKESUB_7_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.


183

00:12:00,449 --> 00:12:01,997
"""

FAKESUB_8_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.


181

00:12:00,449 --> 00:12:01,997
"""

FAKESUB_9_FAIL_INDEX = """249
00:12:51,650 --> 00:12:52,735
Esatto.

00:12:52,904 --> 00:12:54,487
- Non fa sul serio...
- Si' invece.
"""

FAKESUB_0_FAIL_TIME_IF_NOT_B = """1567
-1:26:32,200 --> -1:26:35,060
"un figlio di puttana faceva ruotare la freccetta
e mi prendeva a calci in culo, Eddie.
"""

class FileTest (unittest.TestCase):
    """Test operation on files. """

    def testOkSubs (self):
        options = ["-H", "-M", "-S", "-m", "-n"]
        lenopt = len(options)
        cmdline = ["python", PROGFILE]
        for sub in (FAKESUB_0, FAKESUB_1, FAKESUB_2):
            choosed = cmdline[:]
            back_to = cmdline[:]
            opts = options[:]
            random.shuffle(opts)
            for n in range(random.randint(1, lenopt)):
                o, v = opts.pop(), random.randint(0, 999)
                back_to.append("%s %d" % (o, -v))
                choosed.append("%s %d" % (o, v))
            fpipe = sbp.Popen(["echo", "-n", sub], stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, stdin=fpipe.stdout, stdout=sbp.PIPE)
            new_text = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, "Retcode is %d" % retcode)
            fpipe = sbp.Popen(["echo", "-n", new_text], stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, stdin=fpipe.stdout, stdout=sbp.PIPE)
            orig_text = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, "Retcode is %d" %retcode)
            self.assertEqual(sub, orig_text, "Differences between texts!!!\n"
                             "#%s######\n#%s###" % (sub, orig_text))

    def testFailSubs (self):
        fail_list = [FAKESUB_6_FAIL_INDEX, FAKESUB_7_FAIL_INDEX,
                     FAKESUB_8_FAIL_INDEX,FAKESUB_9_FAIL_INDEX, 
                     FAKESUB_3_FAIL_TIME, FAKESUB_4_FAIL_TIME, 
                     FAKESUB_5_FAIL_TIME, FAKESUB_6_FAIL_TIME,]
        for sub in fail_list:
            fpipe = sbp.Popen(["echo", "-n"], stdout=sbp.PIPE)
            spipe = sbp.Popen(["python", PROGFILE],
                              stdin=fpipe.stdout, stdout=sbp.PIPE)
            out = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, (retcode))

    def testIndex (self):
        for sub_string in (FAKESUB_6_FAIL_INDEX,
                           FAKESUB_7_FAIL_INDEX,
                           FAKESUB_8_FAIL_INDEX, 
                           FAKESUB_9_FAIL_INDEX,):
            sub = StringIO.StringIO(sub_string)
            newsub = csub.SrtSub(sub, sub)
            self.assertRaises(csub.IndexNumError, newsub.main)

    def testUnhandledError (self):
        def  get_error (error):
            def raise_error (*args):
                raise error
            return raise_error
        errors = [TypeError, UnboundLocalError, ValueError,
                  IOError, OSError, SystemError, AttributeError,]
        for error in errors:
            sub = StringIO.StringIO(FAKESUB_0)
            newsub = csub.SrtSub(sub, sub)
            newsub.match_time = get_error(error)
            try:
                newsub.main()
            except Exception, e:
                msg = "it should be %s" % e
                self.assertNotEqual(e, csub.MismatchTimeError, msg)
                self.assertNotEqual(e, csub.IndexNumError, msg)


class ReTest (unittest.TestCase):

    def setUp (self):
        self.subs = csub.SrtSub(None, None)
        self.time_string_ok = ("00:12:56,123", "01:56:00,000", "-12:00:02,999",
                               "00:10:12,010", "-00:44:44,123",)
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
                                "01:562:00,432","1:56:00,000",)
        self.number_string_ok =("1", "01", "0009", "09", "1234567",
                                "-12", "01", "0", "-02", "-93",)
        self.number_string_err =("+097a", "07a",  "0xffffffff", "+", "-",
                                  "-2e10",  "2e10", "stringa",)

    def testReTime (self):
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
        

    def testReNumber (self):
        for string in self.number_string_ok:
            self.assertTrue((self.subs.new_sub_num(string) is not None),
                            "Failed on %s" % string)
        for string in self.number_string_err:
            self.assertRaises(csub.IndexNumError,
                              self.subs.new_sub_num, string)


class TimeTransformTest (unittest.TestCase):

    def setUp (self):
        self.subs = csub.SrtSub(None, None)
        self.subs.ITER_FUNC = self.subs.make_iter_blocks(
            self.subs.text_block, lambda *args: args)
        self.subs._get_func = self.subs.ITER_FUNC.next()
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
        h, m, s, ms = map(int, self.subs.match_time(string_time).group(1, 2, 3, 4))
        secs, ms = self.subs.new_time_tuple(h, m, s, ms)
        nh, nm, ns = self.subs.times_from_secs(secs)
        return self.subs.string_format % (nh, nm, ns, ms)

    def random_time (self, orig_time_string):
        delta_time = [random.randint(-100, 2000) for i in ("h", "m", "s", "n")]
        delta_time.insert(-1, random.randint(-999, 999))
        self.subs.set_delta(*delta_time)
        new_time_string = self.subs.time_block(orig_time_string)[0]
        self.subs.set_delta(*map(int.__neg__, delta_time))
        return self.subs.time_block(new_time_string)[0]

    def testTimeSep (self):
        for string in self.sep_err:
            self.assertRaises(csub.MismatchTimeError,
                              self.subs.time_block, string)

    def testTimeCalc (self):
        self.subs.set_delta(0, 0, 0, 0, 0)
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


class TempFileTest (unittest.TestCase):

    def testTempFileObjects (self):
        tmp_1 = csub.TempFile(None)
        tmp_2 = csub.TempFile(sys.stdin)
        tmp_3 = csub.TempFile(StringIO.StringIO(FAKESUB_0))
        self.assertTrue(hasattr(tmp_1, '_fake'))
        self.assertTrue(hasattr(tmp_2, '_fake'))
        self.assertFalse(hasattr(tmp_3, '_fake'))
        for method in ('close', 'read', 'seek', 'write_back'):
            m1 = inspect.getsourcelines(getattr(tmp_1, method))
            m2 = inspect.getsourcelines(getattr(tmp_2, method))
            m3 = inspect.getsourcelines(getattr(tmp_3, method))
            self.assertEqual(m1, m2, "Not the same method!")
            self.assertEqual(m1, m2, "Not the same method!")
            self.assertNotEqual(m1, m3, "Are the same method!")
            self.assertNotEqual(m2, m3, "Are the same method!")

    def testTempSafety (self):
        orig = StringIO.StringIO(FAKESUB_0_FAIL_TIME_IF_NOT_B)
        sub = StringIO.StringIO(FAKESUB_0_FAIL_TIME_IF_NOT_B)
        tmpfile = csub.TempFile(sub)
        newsub = csub.SrtSub(sub, sub)
        self.assertRaises(csub.MismatchTimeError, newsub.main)
        tmpfile.write_back()
        orig.seek(0);sub.seek(0)
        self.assertEqual(orig.read(), sub.read(), "sub file should be untouched!")


if __name__ == '__main__':
    
    progdir = op.split(op.dirname(op.realpath(__file__)))[0]
    sys.path.insert(0, progdir)
    import csub
    PROGFILE = op.join(op.split(op.dirname(op.realpath(__file__)))[0], 'csub.py')

    file_suite = unittest.TestLoader().loadTestsFromTestCase(FileTest)
    re_suite = unittest.TestLoader().loadTestsFromTestCase(ReTest)
    time_suite = unittest.TestLoader().loadTestsFromTestCase(TimeTransformTest)
    tmp_suite = unittest.TestLoader().loadTestsFromTestCase(TempFileTest)
    tests = unittest.TestSuite([file_suite, re_suite, time_suite, tmp_suite])
    unittest.TextTestRunner(verbosity=2).run(tests)

    for f in glob.glob("%s.py[oc]" % op.splitext(PROGFILE)[0]):
        os.remove(f) 

"""
testFailSubs (__main__.FileTest) ... ok
testIndex (__main__.FileTest) ... ok
testOkSubs (__main__.FileTest) ... ok
testUnhandledError (__main__.FileTest) ... ok
testReNumber (__main__.ReTest) ... ok
testReTime (__main__.ReTest) ... ok
testTimeCalc (__main__.TimeTransformTest) ... ok
testTimeSep (__main__.TimeTransformTest) ... ok
testTempFileObjects (__main__.TempFileTest) ... ok
testTempSafety (__main__.TempFileTest) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.549s

OK
"""
