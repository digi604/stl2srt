#!/usr/bin/env python
# -*- encoding=utf8 -*-
#
# stl2srt A program to convert EBU STL subtitle files in the more common SRT format
#
#    Copyright (C) 2011 Yann Coupin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import struct
import codecs
import logging
import unicodedata

class SRT:
    '''A class that behaves like a file object and writes an SRT file'''
    def __init__(self, pathOrFile):
        if isinstance(pathOrFile, file):
            self.file = pathOrFile
        else:
            self.file = open(pathOrFile, 'wb')
        self.counter = 1
        self.file.write(codecs.BOM_UTF8)

    def _formatTime(self, timestamp):
        return "%02u:%02u:%02u,%03u" % (
            timestamp / 3600,
            (timestamp / 60) % 60,
            timestamp % 60,
            (timestamp * 1000) % 1000
        )

    def write(self, start, end, text):
        text = "\n".join(filter(lambda (x): bool(x), text.split("\n")))
        self.file.write("%0u\n%s --> %s\n%s\n\n" % (self.counter, self._formatTime(start), self._formatTime(end), text.encode('utf8')))
        self.counter += 1

class iso6937(codecs.Codec):
    '''A class to implement the somewhat exotic iso-6937 encoding which STL files often use'''

    identical = set(range(0x20, 0x7e))
    identical |= set((0xa0, 0xa1, 0xa2, 0xa3, 0xa5, 0xa7, 0xab, 0xb0, 0xb1, 0xb2, 0xb3, 0xb5, 0xb6, 0xb7, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf))
    direct_mapping = {
        0x8a: 0x000a, # line break

        0xa8: 0x00a4, # ¤
        0xa9: 0x2018, # ‘
        0xaa: 0x201C, # “
        0xab: 0x00AB, # «
        0xac: 0x2190, # ←
        0xad: 0x2191, # ↑
        0xae: 0x2192, # →
        0xaf: 0x2193, # ↓

        0xb4: 0x00D7, # ×
        0xb8: 0x00F7, # ÷
        0xb9: 0x2019, # ’
        0xba: 0x201D, # ”
        0xbc: 0x00BC, # ¼
        0xbd: 0x00BD, # ½
        0xbe: 0x00BE, # ¾
        0xbf: 0x00BF, # ¿

        0xd0: 0x2015, # ―
        0xd1: 0x00B9, # ¹
        0xd2: 0x00AE, # ®
        0xd3: 0x00A9, # ©
        0xd4: 0x2122, # ™
        0xd5: 0x266A, # ♪
        0xd6: 0x00AC, # ¬
        0xd7: 0x00A6, # ¦
        0xdc: 0x215B, # ⅛
        0xdd: 0x215C, # ⅜
        0xde: 0x215D, # ⅝
        0xdf: 0x215E, # ⅞

        0xe0: 0x2126, # Ohm Ω
        0xe0: 0x00C6, # Æ
        0xe0: 0x0110, # Đ
        0xe0: 0x00AA, # ª
        0xe0: 0x0126, # Ħ
        0xe0: 0x0132, # Ĳ
        0xe0: 0x013F, # Ŀ
        0xe0: 0x0141, # Ł
        0xe0: 0x00D8, # Ø
        0xe0: 0x0152, # Œ
        0xe0: 0x00BA, # º
        0xe0: 0x00DE, # Þ
        0xe0: 0x0166, # Ŧ
        0xe0: 0x014A, # Ŋ
        0xe0: 0x0149, # ŉ

        0xf0: 0x0138, # ĸ
        0xf0: 0x00E6, # æ
        0xf0: 0x0111, # đ
        0xf0: 0x00F0, # ð
        0xf0: 0x0127, # ħ
        0xf0: 0x0131, # ı
        0xf0: 0x0133, # ĳ
        0xf0: 0x0140, # ŀ
        0xf0: 0x0142, # ł
        0xf0: 0x00F8, # ø
        0xf0: 0x0153, # œ
        0xf0: 0x00DF, # ß
        0xf0: 0x00FE, # þ
        0xf0: 0x0167, # ŧ
        0xf0: 0x014B, # ŋ
        0xf0: 0x00AD, # Soft hyphen
    }
    diacritic = {
        0xc1: 0x0300, # grave accent
        0xc2: 0x0301, # acute accent
        0xc3: 0x0302, # circumflex
        0xc4: 0x0303, # tilde
        0xc5: 0x0304, # macron
        0xc6: 0x0306, # breve
        0xc7: 0x0307, # dot
        0xc8: 0x0308, # umlaut
        0xca: 0x030A, # ring
        0xcb: 0x0327, # cedilla
        0xcd: 0x030B, # double acute accent
        0xce: 0x0328, # ogonek
        0xcf: 0x030C, # caron
    }


    def decode(self, input):
        output = []
        state = None
        count = 0
        for char in input:
            char = ord(char)
            # End of a subtitle text
            if char == 0x8f:
                break
            count += 1
            if not state and char in range(0x20, 0x7e):
                output.append(char)
            elif not state and char in self.direct_mapping:
                output.append(self.direct_mapping[char])
            elif not state and char in self.diacritic:
                state = self.diacritic[char]
            elif state:
                combined = unicodedata.normalize('NFC', unichr(char) + unichr(state))
                if combined and len(combined) == 1:
                    output.append(ord(combined))
                state = None
        return (''.join(map(unichr, output)), len(input))

    def search(self, name):
        if name in ('iso6937', 'iso_6937-2'):
            return codecs.CodecInfo(self.encode, self.decode, name='iso_6937-2')

    def encode(self, input):
        pass

codecs.register(iso6937().search)

class STL:
    '''A class that behaves like a file object and reads an STL file'''

    GSIfields = 'CPN DFC DSC CCT LC OPT OET TPT TET TN TCD SLR CD RD RN TNB TNS TNG MNC MNR TCS TCP TCF TND DSN CO PUB EN ECD UDA'.split(' ')
    TTIfields = 'SGN SN EBN CS TCIh TCIm TCIs TCIf TCOh TCOm TCOs TCOf VP JC CF TF'.split(' ')


    def __init__(self, pathOrFile, offset):
        self.offset = float(offset)/1000
        if isinstance(pathOrFile, file):
            self.file = pathOrFile
        else:
            self.file = open(pathOrFile, 'rb')
        self._readGSI()

    def _readGSI(self):
        self.GSI = dict(zip(
            self.GSIfields,
            struct.unpack('3s8sc2s2s32s32s32s32s32s32s16s6s6s2s5s5s3s2s2s1s8s8s1s1s3s32s32s32s75x576s', self.file.read(1024))
        ))
        GSI = self.GSI
        logging.debug(GSI)
        #self.gsiCodePage = 'cp%s' % GSI['CPN']
        if GSI['DFC'] == 'STL25.01':
            self.fps = 25
        elif GSI['DFC'] == 'STL30.01':
            self.fps = 30
        else:
            raise Exception('Invalid CPN')
        self.codePage = {
            '00': 'iso_6937-2',
            '01': 'iso-8859-5',
            '02': 'iso-8859-6',
            '03': 'iso-8859-7',
            '04': 'iso-8859-8',
        }[GSI['CCT']]
        self.numberOfTTI = int(GSI['TNB'])
        self.startTime = self.__timecodeDecode(
            int(GSI['TCF'][0:2]),
            int(GSI['TCF'][2:4]),
            int(GSI['TCF'][4:6]),
            int(GSI['TCF'][6:8])
        ) - self.offset
        logging.debug(self.__dict__)

    def __timecodeDecode(self, h, m, s, f):
        return 3600 * h + 60 * m + s + float(f) / self.fps

    def _readTTI(self):
        while (True):
            tci = None
            tco = None
            txt = []

            while (True):
                data = self.file.read(128)
                if not data:
                    raise StopIteration()
                TTI = dict(zip(
                    self.TTIfields,
                    struct.unpack('<BHBBBBBBBBBBBBB112s', data)
                ))
                logging.debug(TTI)
                # if comment skip
                if TTI['CF']:
                    continue
                if not tci:
                    tci = self.__timecodeDecode(TTI['TCIh'], TTI['TCIm'], TTI['TCIs'], TTI['TCIf']) - self.startTime
                    tco = self.__timecodeDecode(TTI['TCOh'], TTI['TCOm'], TTI['TCOs'], TTI['TCOf']) - self.startTime
                txt += TTI['TF'].decode(self.codePage).strip()
                if TTI['EBN'] == 255:
                    # skip empty subtitles and those before the start of the show
                    if txt and tci >= 0:
                        return (tci, tco, ''.join(txt))
                    break

    def __iter__(self):
        return self

    def next(self):
        return self._readTTI()

if __name__ == '__main__':
    from optparse import OptionParser
    import sys

    parser = OptionParser(usage = 'usage: %prog [options] input output')
    parser.add_option('-d', '--debug', dest='debug_level', action='store_const', const=logging.DEBUG, default=logging.ERROR)
    parser.add_option('-o', '--offset', dest='offset', help='start offset in milliseconds', default=0)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    logging.basicConfig(level=options.debug_level)

    stl = STL(args[0], int(options.offset))
    c = SRT(args[1])
    for sub in stl:
        (tci, tco, txt) = sub
        c.write(tci, tco, txt)
