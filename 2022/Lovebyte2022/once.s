
	.include	"globals.i"

	.import	__SCREEN0_START__
	.import	_frame0000
	.import	main


	;; EXEHDR and ONCE are in the ONCE memory, it will be probably overwritten once main starts.
	.segment	"EXEHDR"
	.word	next_line
	.word	7		; Line number
	.byte	$9e		; SYS
	.byte	"(2071) : ",$8f," VCC"
next_line:	.byte	0,0,0
	jmp	once

	.bss
scratch:	.res	1	; Scratch area.

	.segment	"ONCE"	; Data part.
spritedata:			; This is the sprite that will colour the heart!
	.repeat	8
	.byte	$FF,0,0
	.endrepeat
	.res	3*16,0

	.segment	"ONCE"
once:
	sei
	cld
	lda	$30c            ; If crunched A may contained garbage.
	cmp	#0		; To get the flags aka is A zero?
	bne	nocopy
	ldx	#127
l2:	lda	y_sine,x
	sta	SINEAREA,x
	dex
	bpl	l2
nocopy:
	lda	#0
	jsr	$1000

	ldx	#0
l1:
	.repeat 4,I
	lda	_frame0000+2+2002*4+I*$100,x
	sta	__SCREEN0_START__+I*$100,x
	lda	_frame0000+2+2002*4+1000+I*$100,x
	sta	$D800+I*$100,x
	.endrepeat
	dex
	bne	l1
	;; Copy heart.
	ldx	#$3f-1		; 63 Bytes.
l3:	lda	spritedata,x	; Copy byte to sprite buffer.
	sta	$340,x
	dex			; And another one.
	bpl	l3
	lda	#$340/64
	sta	$7ff		; Sprite poiner of sprite seven.
	lda	#$29		; Sprite X position. MSB below.
	sta	$d00e
	lda	#50+10*8
	sta	$d00f
	lda	#%10000000
	sta	$d010		; MSB on.
	sta	$d015		; Enable sprite seven.
	sta	$d01b		; And put it in the background.
	lda	#2		; Colour is red.
	sta	$d027+7
	jmp	main
