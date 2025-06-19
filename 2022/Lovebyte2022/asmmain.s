	.include	"LAMAlib.inc"
	.include	"globals.i"

	.import	_frame0000, _frame0001, _frame0002
	.import __SCREEN0_START__
	.import advance_display_state
frontback=1	   ;set to 1 to have front-back effect
delayrastermove=1  ;set to 1 to have the animation waiting first

musicplay=$1003
;;; Every n-th frame an update of the frames is performed.
NTHFRM=4

	.export	main

	.zeropage
ptr1:	.res	2

	.code
	.proc	update_lbytes
	dec	counter
	bpl	end
	lda	#NTHFRM
	sta	counter
	ldx	index
	inx
	cpx	#(hip-lop)
	if ge
	  ldx     #00
	endif
	stx	index
	lda	lop,x
	sta	ptr1
	lda	hip,x
	sta	ptr1+1
	ldy	#250
l1:	lda	(ptr1),y
	sta	__SCREEN0_START__,y
	dey
	bne	l1
	lda	ptr1
	clc
	adc	#<1000
	sta	ptr1
	lda	ptr1+1
	adc	#>1000
	sta	ptr1+1
	ldy	#250
l2:	lda	(ptr1),y
	sta	$d800,y
	dey
	bne	l2
end:	rts

	.data
counter:	.byte	NTHFRM
index:	.byte	0

	.rodata
	.define	FRAMES	_frame0000+2,_frame0000+2, _frame0000+2,_frame0000+2, _frame0000+2,_frame0000+2,_frame0001+2, _frame0002+2, _frame0002+2, _frame0002+2, _frame0001+2
	;; Keep hip and lop together as this also defines the overall number of frames for deciding when the index needs to restart.
lop:	.lobytes	FRAMES
hip:	.hibytes	FRAMES
	.endproc

	.code
	.proc	irq_alike
	jsr	musicplay
	jmp	update_lbytes
	.endproc

	.code
main:
.if frontback>0
        memset $0800,$0fff,0    ;ensure the alternative charset is empty
        ;memset $d918,$d98f,0    ;paint the part of the screen black containing the hidden line
.endif
	ldx #y_sine_size-4
mainloop:    
	sei
	lda $2A6
	if ne
	  jmp pretty_PAL_routine
	endif

; =====================================================================================
; Dirty routine using raster polling
; much shorter code and shows also a rasterbars on NTSC (with some tearing)
; =====================================================================================

; dirty NTSC routine
wait_upper_raster:
	bit $d011
	bmi wait_upper_raster

	ldy SINEAREA,x	;the line where the next rasterline will start
.if delayrastermove>0
sm_inx:
	nop	;later this becomes inx
.else
	inx
.endif
	cpx #y_sine_size
	bcc noreset
	ldx #00
noreset:
.if frontback>0
	lda #%00010100  ;$400 Sceen, $1000 Charset
	cpx #y_sine_size/2
	bcc firsthalf
	lda #%00010010  ;$400 Screen, $800 Charset
firsthalf:
	sta charmode_buffer
.endif
	store X
;	nop	;magic nop to improve timing
wait0:
        cpy $d012
        bne wait0

        ldx #colorsend-colors-1   
loop1:	lda colors,x    ;next color

.if frontback>0
	store X
	ldx %00010100
	cmp #00		;check if we have color 0
	beq keepx	;keep value of x if this is the case
charmode_buffer=*+1
	ldx #2
keepx:
.endif
wait1:
        cpy $d012
        bcs wait1        ;wait until rasterline Y has passed

        sta $d020        
        sta $d021

.if frontback>0
	stx $d018	 ;possibly change charset
.endif
        iny              ;next rasterline = y+2
        iny
.if frontback>0
	restore X
.endif
        dex
        bpl loop1
.if frontback>0
	poke $d018,%00010100
.endif

	ldy #134	;wait for somewhere down in the border
wait2:	cpy $d012
	bne wait2

;	inc $d020
	jsr	irq_alike
;	dec $d020
	jsr advance_display_state

.if delayrastermove>0
	dec waitcounter
	bne :+
	poke sm_inx,$e8	;opcode of inx
:
.endif
use_remaining_rastertime:
	lda #100
	cmp $d012	
	bcc use_remaining_rastertime

lowerhalf:
	restore X
        jmp mainloop

waitcounter: .byte 225	;a value of 50 means 1 second delay

colors:
        .byte $00
        .byte $07,$07,$0a,$08,$02
        .byte $02,$08,$0a,$07,$07
colorsend:

; =====================================================================================
; Pretty PAL routine using a stable raster
; the code is in srfb and rasterbars.inc
; =====================================================================================

pretty_PAL_routine:
	.import install_rasterbars,sm_inx2
	;pokew music_routine,musicplay
	poke sm_inx2,$ea	;stop rasterbar at beginning
	jsr install_rasterbars

	do
	  ldy #134	;wait for somewhere down in the border
wait3:	  cpy $d012
	  bne wait3
	  jsr	irq_alike
	  jsr advance_display_state
.if delayrastermove>0
	dec waitcounter
	if eq
	  poke sm_inx2,$e8	;opcode of inx
        endif
.endif
	loop
