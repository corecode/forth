	.text
.macro NEXT
	lodsl
	jmp *%eax
.endm

forth_reset:
	movl $dataspace,UP
	movl $corewords,LAST
	ret

forth_run:
	movl %esp,STACK
	movl $RSTACK_end,%ebp

        .bss
	.align 4,0
RSTACK:
	.fill 64,4,0
RSTACK_end:
dataspace:
	.fill 256,4,0

UP:	.long 0
STACK:	.long 0
LAST:	.long 0
