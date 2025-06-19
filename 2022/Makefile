#! /usr/bin/make -f

CC=cl65
CFLAGS=-Os
AS=ca65
ASFLAGS=$(ASDEBUG) -tc64
LD=cl65
LDFLAGS=-C memorymap.cfg

.PHONY:	all run clean release

all:	lovebyte2022

run:	lovebyte2022
	x64 $<

release: lovebyte2022-release.prg

clean:
	rm -f lovebyte2022 *.o *.map *.labels

lovebyte2022:	asmmain.o LoveByte2022_PETSCII.o once.o globals.o srfb.o wipe-effect.o
	$(LD) -m $@.map -Ln $@.labels $(LDFLAGS) -o $@ $+ LAMAlib.lib

listart-tmp.prg: LoveByte2022_ListArt.c
	python PETSCII2BASIC.py -p1 -fLISTSYS -o $@ $<

lovebyte2022-release.prg: lovebyte2022 LoveByte2022_ListArt.c
	python PETSCII2BASIC.py -p1 -fLISTSYS -o tmp1.prg LoveByte2022_ListArt.c
	exomizer sfx sys -Di_load_addr=2198 -C -B lovebyte2022 -o tmp2.prg
	dd if=tmp2.prg bs=1 skip=2 of=tmp3.prg  >nul 2>&1
	cat tmp1.prg tmp3.prg > lovebyte2022-release.prg
	rm tmp1.prg tmp2.prg tmp3.prg
