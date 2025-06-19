#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## Parse PETSCII format from
## Marc's PETSCII editor
## and generate various outputs
## - BASIC print commands
## - A complete viewer in BASIC
## - BASIC data lines
##
## this code is released under a CC-0 license
## by Wil in November 2020
## Version 1.0
##

from __future__ import print_function
import argparse
import sys
import struct

basic_prg = []
codelines = []
basic_start = 0x801
lastptr = -1

CHR_QUOTE = 0x22
CHR_UP = 0x91
CHR_DOWN = 0x11
CHR_LEFT = 0x9d
CHR_RIGHT = 0x1d
CHR_DELETE = 0x14
CHR_RETURN = 0x0d
CHR_SHIFTRETURN = 0x8d
CHR_COMMA = 0x2c
CHR_SPACE = 0x20
CHR_COLORCODES = [
    0x90, #BLK
    0x05, #WHT
    0x1c, #RED
    0x9f, #CYN
    0x9c, #PUR
    0x1e, #GRN
    0x1f, #BLU
    0x9e, #YEL
    0x81, #ORANGE
    0x95, #BROWN
    0x96, #LRED
    0x97, #DGRAY
    0x98, #MGRAY
    0x99, #LGRN
    0x9a, #LBLU
    0x9b, #LGRAY
    ]
CHR_RVSON = 0x12
CHR_RVSOFF = 0x92

TOKEN_PRINT = 0x99
TOKEN_POKE = 0x97
TOKEN_CHR = 0xc7
TOKEN_DATA = 0x83
TOKEN_PLUS = 0xAA
TOKEN_EQ = 0xB2
TOKEN_AND = 0xAF
TOKEN_OR = 0xB0
TOKEN_GET = 0xA1
TOKEN_IF = 0x8B
TOKEN_THEN = 0xA7
TOKEN_SYS = 0x9e
TOKEN_REM = 0x8f

ASM_INDENT = '        '

QUOTESTR = [TOKEN_CHR, ord('('), ord('3'), ord('4'), ord(')'), TOKEN_PLUS, TOKEN_CHR, ord('('), ord('2'), ord('0'), ord(')'), TOKEN_PLUS,
            TOKEN_CHR, ord('('), ord('3'), ord('4'), ord(')')]

SPACES = [chr(32),chr(96)]

QUOTELST = [CHR_QUOTE,CHR_QUOTE,CHR_DELETE]

def load_petscii_c(filename):
    frames = []
    with open(filename) as fp:
        while True:
            tmp = fp.readline()
            if tmp[:7] == '// META':
                break

            # parse border and background color

            (bordercol, bgcol) = [int(x) for x in
                                  fp.readline().strip().rstrip(','
                                  ).split(',')]

            # parse character values

            tmp = ''
            for x in range(25):
                tmp = tmp + fp.readline().strip()
            chars = [int(x) for x in tmp.rstrip(',').split(',')]

            # parse color values

            tmp = ''
            for x in range(25):
                tmp = tmp + fp.readline().strip()
            cols = [int(x) for x in tmp.rstrip(',').split(',')]
            tmp = fp.readline()
            petscii = [bordercol, bgcol, chars, cols]
            frames.append(petscii)
    return frames


def saveBasPrg(filename):
    outfile = open(filename, 'wb')

    # write startaddress

    outfile.write(struct.pack('<H', 0x801))
    for b in basic_prg:
        outfile.write(struct.pack('B', b))


def closeLine():
    global lastptr, basic_prg
    if lastptr >= 0:
        addr = len(basic_prg) + 0x801
        basic_prg[lastptr] = addr & 0xFF
        basic_prg[lastptr + 1] = addr >> 8
        lastptr = -1
        basic_prg += [0]


def closePrg():
    global basic_prg
    closeLine()
    basic_prg += [0, 0]


def addLine():
    global linenr, basic_prg, lastptr
    closeLine()
    lastptr = len(basic_prg)
    basic_prg += [0, 0]
    basic_prg += [linenr & 0xFF]
    basic_prg += [linenr >> 8]
    oldlinenr = linenr
    linenr += lineInc
    return oldlinenr


def addDATA():
    global basic_prg
    basic_prg += [TOKEN_DATA]

def addREM():
    global basic_prg
    basic_prg += [TOKEN_REM]

def addHackedREM():
    global basic_prg
    addREM()
    basic_prg += [CHR_QUOTE,CHR_SHIFTRETURN,CHR_UP]

def addPRINT():
    global basic_prg
    basic_prg += [TOKEN_PRINT]


def addPOKE(a, b):
    global basic_prg
    basic_prg += [TOKEN_POKE]
    addNumber(a)
    addChars(',')
    addNumber(b)

def addSYS(a):
    global basic_prg
    basic_prg += [TOKEN_SYS]
    addNumber(a)

def addNumber(n):
    addChars(str(n))


def addQuotedString(str):
    global basic_prg
    basic_prg += [CHR_QUOTE]
    basic_prg += str
    basic_prg += [CHR_QUOTE]


def addString(str):
    global basic_prg
    basic_prg += str


def addChars(s):
    global basic_prg
    for ch in s:
        basic_prg += [ord(ch)]


def addByte(b):
    global basic_prg
    basic_prg += [b]


def dollarHex(n):
    return '$' + hex(n)[2:]


def removeByte():
    global basic_prg
    last_byte = basic_prg[-1]
    del basic_prg[-1]
    return last_byte


def decodeLine(f, y):
    lastlinehack = False
    if y < 0:
        y = -y
        lastlinehack = True
        firstlinepart = []
    currcol = -1
    rev = False
    full = True
    c = []
    empty = True
    for x in range(40):
        char = f[2][x + y * 40]
        col = f[3][x + y * 40]
        if rev or char != 32 and char != 96:
            empty = False
            if col != currcol:
                if lastlinehack and x == 39:
                    ext1 += [CHR_COLORCODES[col]]
                else:
                    c += [CHR_COLORCODES[col]]
                currcol = col
        v = char > 0x7F
        c2 = char
        char = char & 0x7F
        char = char - 32 + (char & 96) + (char < 32) * 96
        if rev - v:
            if lastlinehack and x == 39:
                if v:
                    ext1 += [CHR_RVSON]
                else:
                    ext1 += [CHR_RVSOFF]
            else:
                if v:
                    c += [CHR_RVSON]
                else:
                    c += [CHR_RVSOFF]
            rev = v
        if char == 0x22:
            if targetformat == 'data':
                c += [39]  # in data lines we need to replace double quotes with single quotes, sorry
            else:
                c += [0x22, ord('Q'), ord('$'), 0x22]
        else:
            c += [char]
        if lastlinehack:
            if x == 37:
                firstlinepart = c
                c = []
            if x == 38:
                ext1 = c
                c = []
    if rev:
        c += [CHR_RVSOFF]
    elif not lastlinehack:
        while len(c) > 0 and (c[-1] == 32 or c[-1] == 96):
            del c[-1]
            full = False
    if lastlinehack:
        return (firstlinepart, ext1, c)
    if empty:
        return ([], False)
    else:
        return (c, full)

def getLastLineNotEmpty(f):
    for lastline in range(24,-1,-1):
        (c, full) = decodeLine(f, lastline)
        if not c == []:
            return lastline
        #if not all(c in SPACES for c in enteredpass1):
        #    return lastline
    return -1

def convertPETSCII2DATA(frames):
    global linenr, lineInc
    for f in frames:
        for y in range(25):
            (c, full) = decodeLine(f, y)
            addLine()
            addDATA()
            addQuotedString(c)
            closeLine()
    closePrg()

def convertPETSCII2LIST(frames,sysflag):
    global linenr, lineInc, basic_prg
    if sysflag:
        toadd = [chr(TOKEN_SYS),'1','2','3','4',':']
    else:
        toadd= []
    prevlineno=linenr    
    for f in frames:
        currentlineno=linenr
        lastline = getLastLineNotEmpty(f)
        if lastline == -1:
            continue
        for y in range(lastline+1):
            (c, full) = decodeLine(f, y)
            addLine()
            addChars(toadd)
            addHackedREM()
            toCover=4+len(str(linenr))
            if toadd!=[]:
                toCover+=8
            toadd=[]
            addString(c)
            if (len(c)<toCover):
                addString([CHR_SPACE]*(toCover-len(c)))
            if y==lastline:
                addByte(CHR_COLORCODES[14])
            closeLine()
    closePrg()
    if sysflag:
      basic_prg[5:9]=[ord(x) for x in str(0x801+len(basic_prg))]

def convertPETSCII2PRINT(frames):
    global linenr, lineInc
    bordercol = -1
    bgcol = -1
    prevlineno=linenr
    for f in frames:
        currentlineno=linenr
        if f[0] != bordercol or f[1] != bgcol:
            bordercol = f[0]
            bgcol = f[1]
            addLine()
            addPOKE(53280, bordercol)
            addChars(':')
            addPOKE(53281, bgcol)
            if 0x22 in f[2] or 128 + 0x22 in f[2]:
                addChars(':Q$')
                addString([TOKEN_EQ])
                addString(QUOTESTR)
            closeLine()
        toadd = [147]  # clrscr
        lastlinehack = False
        for y in range(25):
            (c, full) = decodeLine(f, y)
            if c == []:
                toadd += [0x11]  # crsr down
                continue
            addLine()
            addPRINT()
            if targetformat == 'basicprg' and y == 24 and full:
                # we need to introduce a hack to avoid screen scrollin
                # flip last two characters and colors
                (f[2][38 + y * 40], f[2][39 + y * 40]) = (f[2][39 + y
                        * 40], f[2][38 + y * 40])
                (f[3][38 + y * 40], f[3][39 + y * 40]) = (f[3][39 + y
                        * 40], f[3][38 + y * 40])
                (c, ext1, ext2) = decodeLine(f, -y)
                lastlinehack = True
            addQuotedString(toadd + c)
            toadd = []
            if lastlinehack:
                addChars(';')
                closeLine()
                addLine()
                addPRINT()
                addQuotedString(toadd + ext1 + [CHR_LEFT])
                addByte(TOKEN_CHR)
                addChars('(148)')
                addQuotedString(ext2)
                addChars(';')
            elif full or y == 24:
                addChars(';')
            closeLine()
        if targetformat == 'basicprg':
            currentline = addLine()
            addByte(TOKEN_GET)
            addChars('A$:')
            addByte(TOKEN_IF)
            addChars('A$')
            addByte(TOKEN_EQ)
            addChars('""')
            addByte(TOKEN_THEN)
            addChars(str(currentline))
            closeLine()
            if len(frames)>1:
                #add code for flipping back
                addLine()
                addByte(TOKEN_IF)
                addChars('A$')
                addByte(TOKEN_EQ)
                addQuotedString([CHR_LEFT])
                addByte(TOKEN_OR)
                addChars('A$')
                addByte(TOKEN_EQ)
                addQuotedString([CHR_UP])
                addByte(TOKEN_THEN)
                if prevlineno<currentlineno:
                    addChars(str(prevlineno))
                else:
                    addChars(str(currentline))                
                closeLine()            
        prevlineno=currentlineno
    closePrg()

def saveAsmPrg(filename):
    outfile = open(filename, 'w')
    for l in codelines:
        outfile.write(l + '\n')
    outfile.close()


def loadPETSCII(filename):
    frames = load_petscii_c(filename)
    if args.page and args.page > 0:
        return [frames[args.page - 1]]
    else:
        return frames


# Parse command-line arguments

parser = \
    argparse.ArgumentParser(description='Convert a PETSCII image that was designed using Marq’s PETSCII Editor to BASIC code.'
                            )
parser.add_argument('filename', help='File to be converted.',
                    default='clocktower50.c')
parser.add_argument('-o', '--outfile', help='save converted image' , default='outfile.prg')
parser.add_argument('-p', '--page', nargs='?', type=int, const=0,
                    help='select a specific page from the PETSCII source, otherwise all pages are converted. Page numbers start at 1')
parser.add_argument('-l', '--linenumber',
                    help='select starting linenumber for BASIC program, default=100'
                    , default=100)
parser.add_argument('-i', '--increment',
                    help='select starting increment for linenumbers, default=5'
                    , default=5)
parser.add_argument('-f', '--format',
                    help='select output format: BASIC, BASICPRG, DATA, LIST, LISTSYS'
                    , default='basicprg')

args = parser.parse_args()

targetformat = 'basic'
sysflag = False
if args.format:
    if args.format.lower() == 'basic':
        targetformat = 'basic'
    elif args.format.lower() == 'basicprg':
        targetformat = 'basicprg'
    elif args.format.lower() == 'data':
        targetformat = 'data'
    elif args.format.lower() == 'list':
        targetformat = 'list'
    elif args.format.lower() == 'listsys':
        targetformat = 'list'
        sysflag = True
    else:
        sys.stderr.write('Unknown or unsupported format, please specify BASIC, BASICPRG, or DATA.')
        sys.exit(1)

if args.outfile:
    outfile = args.outfile
else:
    outfile = '.'.join(args.filename.split('.')[:-1]) + '.bas.prg'
    print(outfile)
linenr = args.linenumber
lineInc = args.increment

frames = loadPETSCII(args.filename)
if targetformat == 'basic' or targetformat == 'basicprg':
    convertPETSCII2PRINT(frames)
    saveBasPrg(outfile)
elif targetformat == 'data':
    convertPETSCII2DATA(frames)
    saveBasPrg(outfile)
elif targetformat == 'list':
    convertPETSCII2LIST(frames,sysflag)
    saveBasPrg(outfile) 
