; -*- mode: asm -*-

	;;  Here we may put the sine data.
	.define	SINEAREA	$C000

	;; 128 Byte of sine data.
	.import	y_sine, y_sine_end
	.importzp y_sine_size
