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
import copy
import random
import inspect
import unittest
import StringIO
import subprocess as sbp
import shlex
import operator


PROGFILE = 'csub.py'
DATA_DIR = 'data'
CWD = op.dirname(op.realpath(__file__))


SRT_FAKESUB_0 = """1567
01:26:32,200 --> 01:26:35,060
un figlio di puttana faceva ruotare la freccetta
e mi prendeva a calci in culo, Eddie.

1568
01:26:35,830 --> 01:26:38,430
Poi dovevo andare a scuola e vedere
gli altri bambini mangiare cibo vero.

1569
01:26:38,500 --> 01:26:41,310
Dovevo vederli mangiare burro d'arachidi
gelatina, carne, pasta,

1570
01:26:41,380 --> 01:26:44,140
prosciutto e formaggio.
Io avevo un dannato sandwich di Pongo.

1571
01:26:45,730 --> 01:26:48,050
Poi, per dessert, tiravano fuori
una merendina

1572
01:26:48,190 --> 01:26:50,180
Ed io dovevo mangiarmi una dannata Slinky?
"""

SRT_FAKESUB_1 = """242
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

SRT_FAKESUB_2 = """7
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

SRT_FAKESUB_3_FAIL_TIME = """170
00:11:21,220 --> 00:11:23,897
Sono perfettamente a mio agio
con i fluidi corporei...

171

sangue, muco, lacrime...
"""

SRT_FAKESUB_4_FAIL_TIME = """172
00:11:26,316 --> 00:11:28,965
ma con le emozioni che
li accompagnano...

173
non ci so fare altrettanto bene.

00:11:32,015 --> 00:11:33,031
Dexter...
"""

SRT_FAKESUB_5_FAIL_TIME = """182
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

SRT_FAKESUB_6_FAIL_TIME = """172
00:11:26,316 --> 00:11:28,965
ma con le emozioni che
li accompagnano...

173
non ci so fare altrettanto bene.

00:11:32,015 --> 00:11:33,031
Dexter...
"""

SRT_FAKESUB_6_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.

error here!

00:12:00,449 --> 00:12:01,997
"""

SRT_FAKESUB_7_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.


183

00:12:00,449 --> 00:12:01,997
"""

SRT_FAKESUB_8_FAIL_INDEX = """182
00:11:57,011 --> 00:12:00,414
E' sempre perso nei suoi pensieri,
e, quando mi parla, dice solo bugie.


181

00:12:00,449 --> 00:12:01,997
"""

SRT_FAKESUB_9_FAIL_INDEX = """249
00:12:51,650 --> 00:12:52,735
Esatto.

00:12:52,904 --> 00:12:54,487
- Non fa sul serio...
- Si' invece.
"""

SRT_FAKESUB_0_FAIL_TIME_IF_NOT_B = """1567
-1:26:32,200 --> -1:26:35,060
un figlio di puttana faceva ruotare la freccetta
e mi prendeva a calci in culo, Eddie.
"""

ASS_FAKESUB_0 = '''Dialogue: 0,0:01:02.25,0:01:04.75,Default,,0000,0000,0000,,Che bello vedervi, è una figata!
Dialogue: 0,0:01:04.85,0:01:06.77,Default,,0000,0000,0000,,Vi divertirete stasera, è un bello spettacolo.
Dialogue: 0,0:01:06.80,0:01:10.17,Default,,0000,0000,0000,,È sempre stato bello, se stasera farà schifo potrebbe essere colpa vostra.
'''

ASS_FAKESUB_1 = """Dialogue: 0,0:03:43.14,0:03:44.82,Default,,0000,0000,0000,,Fottuti... vedete...
Dialogue: 0,0:03:44.93,0:03:48.86,Default,,0000,0000,0000,,...il rock cristiano è una tale fottuta assurdità, in questo mondo...
Dialogue: 0,0:03:58:08,0:03:59.90,Default,,0000,0000,0000,,"È il mio Salvatore..."
Dialogue: 0,0:04:06:72,0:04:09.02,Default,,0000,0000,0000,,Questo non è rock'n'roll!
Dialogue: 0,0:04:09.27,0:04:12:84,Default,,0000,0000,0000,,È merda degna di un club giovanile di ping pong!
Dialogue: 0,0:04:13.61,0:04:17:69,Default,,0000,0000,0000,,Il rock'n'roll è: "Sono il diavolo e voglio scoparmi tua madre!"
Dialogue: 0,0:04:28.94,0:04:32.87,Default,,0000,0000,0000,,Ho sempre voluto cantare una di quelle canzoni di Elvis che si fermavano.
Dialogue: 0,0:04:33:33,0:04:34:87,Default,,0000,0000,0000,,Il vero Elvis.
Dialogue: 0,0:04:35.09,0:04:38.08,Default,,0000,0000,0000,,Non quello stronzo grasso che l'ha preso in ostaggio e l'ha mangiato.
"""

ASS_FAKESUB_2_OK_MISC = """
Dialogue: 0,0:08:47.19,0:08:50.97,Default,,0000,0000,0000,,Sapete, per quelli di voi che se la prendono per una cazzo di battuta.
Dialogue: 0,0:09:19.61,0:09:22.99,Default,,0000,0000,0000,,Detto questo, per me la religione è finita, cazzo!
Dialogue: 0,0:09:02.35,0:09:05.32,Default,,0000,0000,0000,,Basta, è fottutamente finita, amici,
Dialogue: 0,1:09:05.55,1:09:08.22,Default,,0000,0000,0000,,è finita, cazzo!
Dialogue: 0,0:09:08.39,0:09:12.96,Default,,0000,0000,0000,,Avete avuto un paio di migliaia di anni, avete mandato tutto a puttane, è finita!
Dialogue: 0,1:09:48.72,1:09:51.56,Default,,0000,0000,0000,,È fottutamente FINITA!
Dialogue: 0,0:09:16.92,0:09:19.54,Default,,0000,0000,0000,,Prendete la vostra Riforma, il vostro Vaticano,
Dialogue: 0,0:08:58.88,0:09:01.83,Default,,0000,0000,0000,,la vostra fottuta Mecca e andatevene affanculo!
Dialogue: 0,0:09:30.17,0:09:34.80,Default,,0000,0000,0000,,Kamikaze, cazzo! Ecco un'ottima idea.
Dialogue: 0,0:09:36.15,0:09:39.50,Default,,0000,0000,0000,,A ogni esplosione c'è un segaiolo in meno.
Dialogue: 0,0:09:42.27,0:09:44.04,Default,,0000,0000,0000,,Fottuti idioti!
Dialogue: 0,0:09:45.12,0:09:47.32,Default,,0000,0000,0000,,Voglio vedere l'istruttore!
Dialogue: 0,0:09:13.12,0:09:16.41,Default,,0000,0000,0000,,"Ok, ragazzi, ve lo mostrerò una volta sola..."
Dialogue: 0,0:09:57.43,0:09:59.06,Default,,0000,0000,0000,,Fottuti cazzoni!
"""

ASS_FAKESUB_3_FAIL_TIME = """
Dialogue: 0,0:06:54.55,0:06:57.83,Default,,0000,0000,0000,,Avete visto il funerale del Papa? Un funerale tranquillo, lo voleva semplice.
Dialogue: 0,0:06:59.64,0:07:01.52,Default,,0000,0000,0000,,Cazzo, era tipo "Ben Hur", vero?
Dialogue: 0,0:07:04.73,0:07:07.09,Default,,0000,0000,0000,,Migliaia di pedofili in velluto rosso.
Dialogue: 0,0:07:20.02,0:07:21.81,Default,,0000,0000,0000,,In realtà era morto da un po'.
Dialogue: 0,0:07:22.49,0:07:23.81,Default,,0000,0000,0000,,4 o 5 anni.
Dialogue: 0,0:07:26.03,0:07:27.86,Default,,0000,0000,0000,,Ma non avevano scelto quello che volevano,
Dialogue: 0,0:07:27.93,0:07:30.136,Default,,0000,0000,0000,,il piccolo fascista fottuto, quindi...
"""

ASS_FAKESUB_4_FAIL_TIME_H = """
Dialogue: 0,0:07:31.07,0:07:33.38,Default,,0000,0000,0000,,Il piccolo Benedetto della fottuta Hitler Jugend.
Dialogue: 0,11:07:35.58,0:07:38.18,Default,,0000,0000,0000,,Stavano aspettando che il suo nome salisse in cima alla lista.
"""

ASS_FAKESUB_5_FAIL_TIME_H = """
Dialogue: 0,0:07:38.35,0:07:41.00,Default,,0000,0000,0000,,Quindi lo hanno trascinato in giro su quella sedia per un paio d'anni.
Dialogue: 0,0:07:43.13,11:07:45.19,Default,,0000,0000,0000,,Lo hanno impagliato con i giornali della domenica...
Dialogue: 0,0:07:46.49,0:07:48.92,Default,,0000,0000,0000,,...due gesuiti dietro di lui gli muovevano la testa...
Dialogue: 0,0:08:08.73,0:08:12.03,Default,,0000,0000,0000,,Oh, dovete tenerli d'occhio, quei fottuti.
"""

ASS_FAKESUB_6_FILE_TIME_IF_NOT_B = """
Dialogue: 0,0:08:35.74,0:08:40.15,Default,,0000,0000,0000,,Nessun bambino è stato molestato nella produzione di questo spettacolo!
Dialogue: 0,0:08:41.95,-1:08:43.35,Default,,0000,0000,0000,,Nessuno è stato ferito.
Dialogue: 0,0:08:43.44,0:08:46.27,Default,,0000,0000,0000,,E non sono state usate vignette islamiche!
"""



class SrtFileTest (unittest.TestCase):
    """Test operation on files. """

    def testOkSrtSubs (self):
        options = ["-H", "-M", "-S", "-m", "-n"]
        lenopt = len(options)
        cmdline = ["python", PROGFILE]
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
            fpipe = sbp.Popen(["echo", "-n", sub], stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, stdin=fpipe.stdout, stdout=sbp.PIPE)
            new_text = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, "Retcode is %d %s %s" % (retcode, cmdline, sub))
            fpipe = sbp.Popen(["echo", "-n", new_text], stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline, stdin=fpipe.stdout, stdout=sbp.PIPE)
            orig_text = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, "Retcode is %d" %retcode)
            self.assertEqual(sub, orig_text, "Differences between texts!!!\n"
                             "#%s######\n#%s###" % (sub, orig_text))

    def testFailSrtSubs (self):
        fail_list = [SRT_FAKESUB_6_FAIL_INDEX, SRT_FAKESUB_7_FAIL_INDEX,
                     SRT_FAKESUB_8_FAIL_INDEX,SRT_FAKESUB_9_FAIL_INDEX, 
                     SRT_FAKESUB_3_FAIL_TIME, SRT_FAKESUB_4_FAIL_TIME, 
                     SRT_FAKESUB_5_FAIL_TIME, SRT_FAKESUB_6_FAIL_TIME,]
        cmdline = ["python", PROGFILE]
        cmdline.append('%s srt' %
                       ('-t' if random.randint(0,1) else '--type'))
        cmdline = shlex.split(' '.join(cmdline))
        for sub in fail_list:
            fpipe = sbp.Popen(["echo", "-n"], stdout=sbp.PIPE)
            spipe = sbp.Popen(cmdline,
                              stdin=fpipe.stdout, stdout=sbp.PIPE)
            out = spipe.communicate()[0]
            retcode = spipe.returncode
            self.assertEqual(retcode, 0, (retcode))

    def testSrtIndex (self):
        for sub_string in (SRT_FAKESUB_6_FAIL_INDEX,
                           SRT_FAKESUB_7_FAIL_INDEX,
                           SRT_FAKESUB_8_FAIL_INDEX, 
                           SRT_FAKESUB_9_FAIL_INDEX,):
            sub = StringIO.StringIO(sub_string)
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
            sub = StringIO.StringIO(SRT_FAKESUB_0)
            newsub = csub.SrtSub(sub, sub)
            newsub.match_time = get_error(error)
            try:
                newsub.main()
            except Exception, e:
                msg = "it should be %s" % e
                self.assertNotEqual(e, csub.MismatchTimeError, msg)
                self.assertNotEqual(e, csub.IndexNumError, msg)


class SrtReTest (unittest.TestCase):

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
        CWD = op.dirname(op.realpath(__file__))
        testsub = op.join(CWD, DATA_DIR, 'fail_sub_1.srt')
        with open(testsub, 'rb') as ts:
            string_sub = ts.read()
        tmpfile = csub.TempFile(testsub)
        with open(tmpfile.filepath, 'rb') as in_file:
            with open(testsub, 'wb') as out_file:
                newsub = csub.SrtSub(in_file, out_file)
                self.assertRaises(csub.MismatchTimeError, newsub.main)
        tmpfile.write_back()
        with open(testsub, 'rb') as ts:
            self.assertEqual(ts.read(), string_sub,
                             "sub file shouldn't be modified!")
        # unsafe mode, no error should be raised:
        with open(testsub, 'rb') as ts:
            outfile = csub.TempFile(testsub)
            with open(outfile.filepath, 'wb') as out:
                newsub = csub.SrtSub(ts, out, True)
                newsub.main()


class AssFileTest (unittest.TestCase):
    def testAssTimeTransform (self):
        subtitles = (ASS_FAKESUB_1,ASS_FAKESUB_2_OK_MISC,)
        _neg = operator.neg
        _r = random.randint
        for i in range(200):
            for subtitle in subtitles:
                sub_orig = StringIO.StringIO(subtitle)
                sub_in = StringIO.StringIO(subtitle)
                sub_out = StringIO.StringIO()
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
            with open(subfile, 'rb') as infile:
                outfile = StringIO.StringIO()
                inst = csub.AssSub(infile, outfile)
                inst.main()
                infile.seek(0)
                outfile.seek(0)
                self.assertEqual(infile.read(), outfile.read())
        for i in range(200):
            for subtitle in subtitles:
                sub_orig = StringIO.StringIO(subtitle)
                sub_in = StringIO.StringIO(subtitle)
                sub_out = StringIO.StringIO()
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
            with open(subfile, 'rb') as infile:
                outfile = StringIO.StringIO()
                inst = csub.AssSub(infile, outfile)
                self.assertRaises(csub.MismatchTimeError, inst.main)
        for subtitle in subtitles:
                sub_in = StringIO.StringIO(subtitle)
                sub_out = StringIO.StringIO()
                inst = csub.AssSub(sub_in, sub_out)
                inst.set_delta()
                self.assertRaises(csub.MismatchTimeError, inst.main)
        # no failure if -b option is enabled
        nofail_sub = ASS_FAKESUB_6_FILE_TIME_IF_NOT_B
        sub_in = StringIO.StringIO(nofail_sub)
        sub_out = StringIO.StringIO()
        inst = csub.AssSub(sub_in, sub_out, True)
        inst.set_delta()
        inst.main()
        # and let's check if the output is the same...
        sub_in.seek(0)
        sub_out.seek(0)
        self.assertEqual(sub_in.read(), sub_out.read())        


def load_tests():
    loader = unittest.TestLoader()
    test_cases = (SrtFileTest, SrtReTest,
                  SrtTimeTransformTest, TempFileTest,
                  AssFileTest,)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)


if __name__ == '__main__':
    progdir = op.split(op.dirname(op.realpath(__file__)))[0]
    sys.path.insert(0, progdir)
    import csub
    PROGFILE = op.join(op.split(op.dirname(op.realpath(__file__)))[0], 'csub.py')
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
    for f in glob.glob("%s.py[oc]" % op.splitext(PROGFILE)[0]):
        os.remove(f) 

