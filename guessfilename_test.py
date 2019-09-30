#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; -*-
# Time-stamp: <2019-09-30 10:08:44 vk>

import unittest
import logging
import tempfile
import os
import os.path
import sys
import re
from guessfilename import GuessFilename
from guessfilename import FileSizePlausibilityException


class TestGuessFilename(unittest.TestCase):

    guess_filename = None

    def handle_logging(self, verbose=False, quiet=False):
        """Log handling and configuration"""

        if verbose:
            FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
            logging.basicConfig(level=logging.DEBUG, format=FORMAT)
        elif quiet:
            FORMAT = "%(levelname)-8s %(message)s"
            logging.basicConfig(level=logging.ERROR, format=FORMAT)
        else:
            FORMAT = "%(levelname)-8s %(message)s"
            logging.basicConfig(level=logging.INFO, format=FORMAT)

    def setUp(self):
        verbose = True
        quiet = False

        CONFIGDIR = os.path.join(os.path.expanduser("~"), ".config/guessfilename")
        sys.path.insert(0, CONFIGDIR)  # add CONFIGDIR to Python path in order to find config file
        try:
            import guessfilenameconfig
        except ImportError:
            print("Could not find \"guessfilenameconfig.py\" in directory \"" + CONFIGDIR + "\".\nPlease take a look at \"guessfilenameconfig-TEMPLATE.py\", copy it, and configure accordingly.")
            sys.exit(1)

        self.handle_logging(verbose, quiet)
        self.guess_filename = GuessFilename(guessfilenameconfig, logging)

    def tearDown(self):
        pass

    def test_rename_file(self):

        tmp_oldfile1 = tempfile.mkstemp()[1]
        oldbasename = os.path.basename(tmp_oldfile1)
        dirname = os.path.abspath(os.path.dirname(tmp_oldfile1))
        newbasename = 'test_rename_file'
        newfilename = os.path.join(dirname, newbasename)

        self.assertTrue(os.path.isfile(tmp_oldfile1))
        self.assertFalse(os.path.isfile(newfilename))

        # return False if files are identical
        self.assertFalse(self.guess_filename.rename_file(dirname, oldbasename, oldbasename, dryrun=True, quiet=True))

        # return False if original file does not exist
        self.assertFalse(self.guess_filename.rename_file(dirname, "test_rename_file_this-is-a-non-existing-file", oldbasename, dryrun=True, quiet=True))

        # return False if target filename does exist
        tmp_oldfile2 = tempfile.mkstemp()[1]
        self.assertTrue(os.path.isfile(tmp_oldfile2))
        oldbasename2 = os.path.basename(tmp_oldfile2)
        self.assertFalse(self.guess_filename.rename_file(dirname, oldbasename, oldbasename2, dryrun=True, quiet=True))
        os.remove(tmp_oldfile2)

        # no change with dryrun set:
        self.assertTrue(self.guess_filename.rename_file(dirname, oldbasename, newbasename, dryrun=True, quiet=True))
        self.assertTrue(os.path.isfile(tmp_oldfile1))
        self.assertFalse(os.path.isfile(newfilename))

        # do rename:
        self.assertTrue(self.guess_filename.rename_file(dirname, oldbasename, newbasename, dryrun=False, quiet=True))
        self.assertFalse(os.path.isfile(tmp_oldfile1))
        self.assertTrue(os.path.isfile(newfilename))

        os.remove(newfilename)

    def test_adding_tags(self):

        self.assertEqual(self.guess_filename.adding_tags(['foo'], ['bar']), ['foo', 'bar'])
        self.assertEqual(self.guess_filename.adding_tags([], ['bar']), ['bar'])
        self.assertEqual(self.guess_filename.adding_tags(['foo'], ['bar', 'baz']), ['foo', 'bar', 'baz'])
        self.assertEqual(self.guess_filename.adding_tags(['foo'], [42]), ['foo', 42])

    def test_derive_new_filename_from_old_filename(self):

        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-03-05 a1 12,34 €.pdf"),
                          "2016-03-05 A1 Festnetz-Internet 12,34€ -- scan bill.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-03-05 A1 12.34 EUR -- finance.pdf"),
                          "2016-03-05 A1 Festnetz-Internet 12.34€ -- finance scan bill.pdf")

        # 2016-01-19--2016-02-12 benutzter GVB 10er Block -- scan transportation graz.pdf
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-03-05 10er.pdf"),
                          "2016-03-05 benutzter GVB 10er Block -- scan transportation graz.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-01-19--2016-02-12 10er GVB.pdf"),
                          "2016-01-19--2016-02-12 benutzter GVB 10er Block -- scan transportation graz.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-01-19--2016-02-12 10er GVB -- foobar.pdf"),
                          "2016-01-19--2016-02-12 benutzter GVB 10er Block -- foobar scan transportation graz.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-01-19 bill foobar baz 12,12EUR.pdf"),
                          "2016-01-19 foobar baz 12,12€ -- scan bill.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2016-03-12 another bill 34,55EUR.pdf"),
                          "2016-03-12 another 34,55€ -- scan bill.pdf")

        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-03-12--2017-09-23 hipster.pdf"),
                         "2017-03-12--2017-09-23 Hipster-PDA vollgeschrieben -- scan notes.pdf")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-03-12--2017-09-23 hipster.png"),
                         "2017-03-12--2017-09-23 Hipster-PDA vollgeschrieben -- scan notes.png")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-03-12-2017-09-23 hipster.png"),
                         "2017-03-12-2017-09-23 Hipster-PDA vollgeschrieben -- scan notes.png")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-03-12-2017-09-23 Hipster.png"),
                         "2017-03-12-2017-09-23 Hipster-PDA vollgeschrieben -- scan notes.png")

        # rec_20171129-0902 A nice recording .wav -> 2017-11-29T09.02 A nice recording.wav
        # rec_20171129-0902 A nice recording.wav  -> 2017-11-29T09.02 A nice recording.wav
        # rec_20171129-0902.wav -> 2017-11-29T09.02.wav
        # rec_20171129-0902.mp3 -> 2017-11-29T09.02.mp3
#        import pdb; pdb.set_trace()
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("rec_20171129-0902 A nice recording .wav"),
                         "2017-11-29T09.02 A nice recording.wav")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("rec_20171129-0902 A nice recording.wav"),
                         "2017-11-29T09.02 A nice recording.wav")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("rec_20171129-0902.wav"),
                         "2017-11-29T09.02.wav")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("rec_20171129-0902.mp3"),
                         "2017-11-29T09.02.mp3")

        # Screenshot_2017-11-29_10-32-12.png
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("Screenshot_2017-11-29_10-32-12.png"),
                         "2017-11-29T10.32.12 -- screenshots.png")
        # Screenshot_2017-11-07_07-52-59 my description.png
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("Screenshot_2017-11-29_10-32-12 my description.png"),
                         "2017-11-29T10.32.12 my description -- screenshots.png")

        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-11-14_16-10_Tue.gpx"),
                         "2017-11-14T16.10.gpx")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-12-07_09-23_Thu Went for a walk .gpx"),
                         "2017-12-07T09.23 Went for a walk.gpx")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("2017-11-03_07-29_Fri Bicycling.gpx"),
                         "2017-11-03T07.29 Bicycling.gpx")

        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180510T090000 ORF - ZIB - Signation -ORIGINAL- 2018-05-10_0900_tl_02_ZIB-9-00_Signation__13976423__o__1368225677__s14297692_2__WEB03HD_09000305P_09001400P_Q4A.mp4"),
                         "2018-05-10T09.00.03 ORF - ZIB - Signation -- lowquality.mp4")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180510T090000 ORF - ZIB - Weitere Signale der Entspannung -ORIGINAL- 2018-05-10_0900_tl_02_ZIB-9-00_Weitere-Signale__13976423__o__5968792755__s14297694_4__WEB03HD_09011813P_09020710P_Q4A.mp4"),
                         "2018-05-10T09.01.18 ORF - ZIB - Weitere Signale der Entspannung -- lowquality.mp4")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180520T201500 ORF - Tatort - Tatort_ Aus der Tiefe der Zeit -ORIGINAL- 2018-05-20_2015_in_02_Tatort--Aus-der_____13977411__o__1151703583__s14303062_Q8C.mp4"),
                         "2018-05-20T20.15.00 ORF - Tatort - Tatort  Aus der Tiefe der Zeit -- highquality.mp4")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180521T193000 ORF - ZIB 1 - Parlament bereitet sich auf EU-Vorsitz vor -ORIGINAL- 2018-05-21_1930_tl_02_ZIB-1_Parlament-berei__13977453__o__277886215b__s14303762_2__WEB03HD_19350304P_19371319P_Q4A.mp4"),
                         "2018-05-21T19.35.03 ORF - ZIB 1 - Parlament bereitet sich auf EU-Vorsitz vor -- lowquality.mp4")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20190902T220000 ORF - ZIB 2 - Bericht über versteckte ÖVP-Wahlkampfkosten -ORIGINALlow- 2019-09-02_2200_tl_02_ZIB-2_Bericht-ueber-v__14024705__o__71528285d6__s14552793_3__ORF2HD_22033714P_22074303P_Q4A.mp4'),
                         '2019-09-02T22.03.37 ORF - ZIB 2 - Bericht über versteckte ÖVP-Wahlkampfkosten -- lowquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20190902T220000 ORF - ZIB 2 - Hinweis _ Verabschiedung -ORIGINALlow- 2019-09-02_2200_tl_02_ZIB-2_Hinweis---Verab__14024705__o__857007705d__s14552799_9__ORF2HD_22285706P_22300818P_Q4A.mp4'),
                         '2019-09-02T22.28.57 ORF - ZIB 2 - Hinweis   Verabschiedung -- lowquality.mp4')
        # NOTE: if you add test cases, you have to add the file name to __init__.py > get_file_size() as well in order to overrule the file size check which would fail in any case!
        # self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename(''),
        #                  '')

        # ORF file not truncated but still without detailed time-stamps
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180608T193000 ORF - Österreich Heute - Das Magazin - Österreich Heute - Das Magazin -ORIGINAL- 13979231_0007_Q8C.mp4"),
                         "2018-06-08T19.30.00 ORF - Österreich Heute - Das Magazin - Österreich Heute - Das Magazin -- highquality.mp4")

        # plausibility checks of file sizes: report plausible sizes
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180608T170000 ORF - ZIB 17_00 - size okay -ORIGINAL- 2018-06-08_1700_tl__13979222__o__1892278656__s14313181_1__WEB03HD_17020613P_17024324P_Q4A.mp4"),
                         "2018-06-08T17.02.06 ORF - ZIB 17 00 - size okay -- lowquality.mp4")
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename("20180608T170000 ORF - ZIB 17_00 - size okay -ORIGINAL- 2018-06-08_1700_tl__13979222__o__1892278656__s14313181_1__WEB03HD_17020613P_17024324P_Q8C.mp4"),
                         "2018-06-08T17.02.06 ORF - ZIB 17 00 - size okay -- highquality.mp4")

        # plausibility checks of file sizes: report non-plausible sizes
        #FIXXME: 2019-09-03: tests disabled because the function was disabled and never raises the expected exception
        #with self.assertRaises(FileSizePlausibilityException, message='file size is not plausible (too small)'):
        #    self.guess_filename.derive_new_filename_from_old_filename("20180608T170000 ORF - ZIB 17_00 - size not okay -ORIGINAL- 2018-06-08_1700_tl__13979222__o__1892278656__s14313181_1__WEB03HD_17020613P_18024324P_Q4A.mp4")
        #with self.assertRaises(FileSizePlausibilityException, message='file size is not plausible (too small)'):
        #    self.guess_filename.derive_new_filename_from_old_filename("20180608T170000 ORF - ZIB 17_00 - size not okay -ORIGINAL- 2018-06-08_1700_tl__13979222__o__1892278656__s14313181_1__WEB03HD_17020613P_18024324P_Q8C.mp4")

        # You might think that it should be 2018-06-09 instead of 2018-06-10. This is caused by different
        # day of metadata from filename (after midnight) and metadata from time-stamp (seconds before midnight):
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20180610T000000 ORF - Kleinkunst - Kleinkunst_ Cordoba - Das Rückspiel (2_2) -ORIGINAL- 2018-06-10_0000_sd_06_Kleinkunst--Cor_____13979381__o__1483927235__s14313621_1__ORF3HD_23592020P_00593103P_Q8C.mp4'),
                         '2018-06-10T23.59.20 ORF - Kleinkunst - Kleinkunst  Cordoba - Das Rückspiel (2 2) -- highquality.mp4')

        # Original ORF TV Mediathek download file names (as a fall-back for raw download using wget or curl):
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('2018-06-14_2105_sd_02_Am-Schauplatz_-_Alles für die Katz-_____13979879__o__1907287074__s14316407_7__WEB03HD_21050604P_21533212P_Q8C.mp4'),
                         '2018-06-14T21.05.06 Am Schauplatz - Alles für die Katz -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('2018-06-14_2155_sd_06_Kottan-ermittelt - Wien Mitte_____13979903__o__1460660672__s14316392_2__ORF3HD_21570716P_23260915P_Q8C.mp4'),
                         '2018-06-14T21.57.07 Kottan ermittelt - Wien Mitte -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('2018-06-14_2330_sd_06_Sommerkabarett - Lukas Resetarits: Schmäh (1 von 2)_____13979992__o__1310584704__s14316464_4__ORF3HD_23301620P_00302415P_Q8C.mp4'),
                         '2018-06-14T23.30.16 Sommerkabarett - Lukas Resetarits: Schmäh (1 von 2) -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('2019-09-29_2255_sd_02_Das-Naturhistor_____14027337__o__1412900222__s14566948_8__ORF2HD_23152318P_00005522P_Q8C.mp4/playlist.m3u8'),
                         '2019-09-29T23.15.23 Das Naturhistor -- highquality.mp4')

        # ORF TV Mediathek as of 2018-11-01: when there is no original filename with %N, I have to use the data I've got
        # see https://github.com/mediathekview/MServer/issues/436
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181028T201400 ORF - Tatort - Tatort_ Blut -ORIGINALhd- playlist.m3u8.mp4'),
                         '2018-10-28T20.14.00 ORF - Tatort - Tatort_ Blut -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181028T201400 ORF - Tatort - Tatort_ Blut -ORIGINALlow- playlist.m3u8.mp4'),
                         '2018-10-28T20.14.00 ORF - Tatort - Tatort_ Blut -- lowquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181022T211100 ORF - Thema - Das Essen der Zukunft -ORIGINALhd- playlist.m3u8.mp4'),
                         '2018-10-22T21.11.00 ORF - Thema - Das Essen der Zukunft -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181022T211100 ORF - Thema - Das Essen der Zukunft -ORIGINALlow- playlist.m3u8.mp4'),
                         '2018-10-22T21.11.00 ORF - Thema - Das Essen der Zukunft -- lowquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181025T210500 ORF - Am Schauplatz - Am Schauplatz_ Wenn alles zusammenbricht -ORIGINALhd- playlist.m3u8.mp4'),
                         '2018-10-25T21.05.00 ORF - Am Schauplatz - Am Schauplatz_ Wenn alles zusammenbricht -- highquality.mp4')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('20181025T210500 ORF - Am Schauplatz - Am Schauplatz_ Wenn alles zusammenbricht -ORIGINALlow- playlist.m3u8.mp4'),
                         '2018-10-25T21.05.00 ORF - Am Schauplatz - Am Schauplatz_ Wenn alles zusammenbricht -- lowquality.mp4')

        # Digital camera from Android
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('IMG_20190118_133928.jpg'),
                         '2019-01-18T13.39.28.jpg')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('IMG_20190118_133928 This is a note.jpg'),
                         '2019-01-18T13.39.28 This is a note.jpg')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('IMG_20190118_133928_Bokeh.jpg'),
                         '2019-01-18T13.39.28 Bokeh.jpg')
        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename('IMG_20190118_133928_Bokeh This is a note.jpg'),
                         '2019-01-18T13.39.28 Bokeh This is a note.jpg')

#        self.assertEqual(self.guess_filename.derive_new_filename_from_old_filename(''),
#                         '')


    def test_film_url_regex(self):

        # check if the defined help text string for a MediathekView film URL matches the corresponding RegEx
        self.assertTrue(re.match(self.guess_filename.FILM_URL_REGEX, self.guess_filename.FILM_URL_EXAMPLE))


    def test_contains_one_of(self):

        self.assertTrue(self.guess_filename.contains_one_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.contains_one_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.contains_one_of("foo bar baz", ['bar']))
        self.assertTrue(self.guess_filename.contains_one_of("foo bar baz", ['ba']))
        self.assertTrue(self.guess_filename.contains_one_of("foo bar baz", ['x', 'ba', 'yuio']))
        self.assertFalse(self.guess_filename.contains_one_of("foo bar baz", ['xfoo']))
        self.assertFalse(self.guess_filename.contains_one_of("foo bar baz", ['xfoo']))
        self.assertFalse(self.guess_filename.contains_one_of("foo bar baz", ['xbar']))
        self.assertFalse(self.guess_filename.contains_one_of("foo bar baz", ['xba']))
        self.assertFalse(self.guess_filename.contains_one_of("foo bar baz", ['x', 'xba', 'yuio']))

    def test_fuzzy_contains_all_of(self):

        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['bar']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['ba']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['foo', "bar", "baz"]))
        self.assertFalse(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['x', 'ba', 'yuio']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['xfoo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['xfoo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['xbar']))
        self.assertFalse(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['xba', "12345"]))
        self.assertFalse(self.guess_filename.fuzzy_contains_all_of("foo bar baz", ['x', 'xba', 'yuio']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo\nbar\nbaz42", ['baz42']))
        self.assertTrue(self.guess_filename.fuzzy_contains_all_of("foo€\nbar\nbaz€42", ['baz€42']))

    def test_fuzzy_contains_one_of(self):

        # comparing exact strings:
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['foo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['bar']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['ba']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['x', 'ba', 'yuio']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['12345']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['12345']))

        # fuzzy similarities:
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xfoo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xfoo']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xbar']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xba']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['x', 'xba', 'yuio']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['7234567880']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['Rundemummer 7234567880']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['Rumdemummer  7234567880']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['Rundemummer 1234581388']))
        self.assertTrue(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['Rumdemummer  1234581388']))

        # fuzzy non-matches:
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", [' 345 ']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['1234581388']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xyz']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['111']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['xby']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("foo bar baz", ['x', 'yyy', 'yuio']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['0987654321']))
        self.assertFalse(self.guess_filename.fuzzy_contains_one_of("Kundennummer 1234567890", ['Rumdemummer  1234555555']))

    def test_has_euro_charge(self):

        self.assertTrue(self.guess_filename.has_euro_charge("12,34EUR"))
        self.assertTrue(self.guess_filename.has_euro_charge("12.34EUR"))
        self.assertTrue(self.guess_filename.has_euro_charge("12,34 EUR"))
        self.assertTrue(self.guess_filename.has_euro_charge("12.34 EUR"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12,34 EUR baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12.34 EUR baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12 EUR baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12EUR baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12.34 EUR baz.extension"))
        self.assertTrue(self.guess_filename.has_euro_charge("12,34€"))
        self.assertTrue(self.guess_filename.has_euro_charge("12.34€"))
        self.assertTrue(self.guess_filename.has_euro_charge("12,34 €"))
        self.assertTrue(self.guess_filename.has_euro_charge("12.34 €"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12,34 € baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12.34 € baz"))
        self.assertTrue(self.guess_filename.has_euro_charge("foo bar 12.34 € baz.extension"))
        self.assertTrue(self.guess_filename.has_euro_charge("2016-03-05 A1 12.34 EUR.pdf"))
        self.assertTrue(self.guess_filename.has_euro_charge("2016-03-05 A1 Festnetz-Internet 12.34 € -- scan finance bill.pdf"))
        self.assertFalse(self.guess_filename.has_euro_charge("1234"))
        self.assertFalse(self.guess_filename.has_euro_charge("foo bar baz"))
        self.assertFalse(self.guess_filename.has_euro_charge("1234eur"))
        self.assertFalse(self.guess_filename.has_euro_charge("foo 12 bar"))
        self.assertFalse(self.guess_filename.has_euro_charge("foo 1234 bar"))
        self.assertFalse(self.guess_filename.has_euro_charge("foo 12,34 bar"))
        self.assertFalse(self.guess_filename.has_euro_charge("foo 12.34 bar"))

    def test_get_euro_charge_from_context(self):

        self.assertEqual(self.guess_filename.get_euro_charge_from_context("xyz foo12,34EURbar xyz", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo12,34EURbar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo12.34EURbar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo12,34€bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo12.34€bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("fooEUR12,34bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("fooEUR12.34bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo€12,34bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo€12.34bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12,34EUR bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12.34EUR bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12,34€ bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12.34€ bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12,34 EUR bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12.34 EUR bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12,34 € bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12.34 € bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo EUR 12,34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo EUR 12.34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo € 12,34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo € 12.34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12,34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo 12.34 bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo ba  12,34  ba bar", "foo", "bar"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("foo xxx 12.34 xxx bar", "foo", "bar"), "12,34")
        self.assertFalse(self.guess_filename.get_euro_charge_from_context("foo xxxx 12.34 xxxx bar", "foo", "bar"))
        self.assertEqual(self.guess_filename.get_euro_charge_from_context("DasinsteinTest2015:EURJahresbeitrag123,45Offen678,90Zahlungenbis03.11.2015sindber",
                                                                           "Offen", "Zahlungen"), "678,90")


    def test_get_euro_charge(self):

        self.assertEqual(self.guess_filename.get_euro_charge("12,34EUR"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("12.34EUR"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("12,34 EUR"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("12.34 EUR"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12,34 EUR baz"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12.34 EUR baz"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12 EUR baz"), "12")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12EUR baz"), "12")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12.34 EUR baz.extension"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("12,34€"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("12.34€"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("12,34 €"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("12.34 €"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12,34 € baz"), "12,34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12.34 € baz"), "12.34")
        self.assertEqual(self.guess_filename.get_euro_charge("foo bar 12.34 € baz.extension"), "12.34")
        self.assertFalse(self.guess_filename.get_euro_charge("1234"))
        self.assertFalse(self.guess_filename.get_euro_charge("foo bar baz"))
        self.assertFalse(self.guess_filename.get_euro_charge("1234eur"))
        self.assertFalse(self.guess_filename.get_euro_charge("foo 12 bar"))
        self.assertFalse(self.guess_filename.get_euro_charge("foo 1234 bar"))
        self.assertFalse(self.guess_filename.get_euro_charge("foo 12,34 bar"))
        self.assertFalse(self.guess_filename.get_euro_charge("foo 12.34 bar"))

    def test_split_filename_entities(self):

        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59.42--2017-04-06T12.13.14 foo bar -- eins zwei.extension"),
                         ("2016-03-05T23.59.42--2017-04-06T12.13.14", "foo bar", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59.42-2017-04-06T12.13.14 foo bar -- eins zwei.extension"),
                         ("2016-03-05T23.59.42-2017-04-06T12.13.14", "foo bar", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59--2017-04-06T12.13 foo - bar.baz - zum -- eins zwei.extension"),
                         ("2016-03-05T23.59--2017-04-06T12.13", "foo - bar.baz - zum", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59.42 foo - bar.baz - zum -- eins zwei.extension"),
                         ("2016-03-05T23.59.42", "foo - bar.baz - zum", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59.42 foo bar -- eins zwei.extension"),
                         ("2016-03-05T23.59.42", "foo bar", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59--2017-04-06T12.13 foo bar -- eins zwei.extension"),
                         ("2016-03-05T23.59--2017-04-06T12.13", "foo bar", ["eins", "zwei"], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59--2017-04-06T12.13 foo bar.extension"),
                         ("2016-03-05T23.59--2017-04-06T12.13", "foo bar", [], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("2016-03-05T23.59 foo bar.extension"),
                         ("2016-03-05T23.59", "foo bar", [], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("foo bar.extension"),
                         (None, "foo bar", [], "extension"))
        self.assertEqual(self.guess_filename.split_filename_entities("foo bar"),
                         (None, "foo bar", [], None))
        self.assertEqual(self.guess_filename.split_filename_entities("foo.bar"),
                         (None, "foo", [], "bar"))
        self.assertEqual(self.guess_filename.split_filename_entities("foo -- bar"),
                         (None, "foo", ["bar"], None))
        self.assertEqual(self.guess_filename.split_filename_entities("foo -- bar.baz"),
                         (None, "foo", ["bar"], "baz"))
        self.assertEqual(self.guess_filename.split_filename_entities(" -- "),
                         (None, ' -- ', [], None))
        self.assertEqual(self.guess_filename.split_filename_entities("."),
                         (None, '.', [], None))

# Local Variables:
# mode: flyspell
# eval: (ispell-change-dictionary "en_US")
# End:
