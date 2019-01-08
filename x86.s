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
	movl $1f,%esi /* return address */
	pushl 8(%esp)
	pushl 16(%esp)
	pushl $EVALUATE
	jmp EXECUTE
2:	movl STACK,%esp
	movl -4(%esp),%eax
	popl %ebp
	ret
1:	.long 2b

        .bss
	.align 4,0
RSTACK:
	.fill 64,4,0
RSTACK_end:
dataspace:
	.fill 256,4,0

STACK:	.long 0
