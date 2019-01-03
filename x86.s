	.text
.macro NEXT
	lodsl
	jmp *%eax
.endm

.GLOBAL forth_reset
forth_reset:
	movl $dataspace,UP_data
	movl $corewords,LAST_data
	ret

.GLOBAL forth_run
forth_run:
	pushl %ebp
	movl %esp,STACK
	movl $RSTACK_end,%ebp
	leal -4(%ebp),%ebp /* store return address */
	movl $1f,(%ebp)
	pushl 8(%esp)
	pushl 16(%esp)
	pushl $EVALUATE
	jmp EXECUTE
1:	movl STACK,%esp
	popl %ebp
	ret

        .bss
	.align 4,0
RSTACK:
	.fill 64,4,0
RSTACK_end:
dataspace:
	.fill 256,4,0

STACK:	.long 0
