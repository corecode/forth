	.text
.macro NEXT
	lodsl
	jmp *%eax
.endm

forth_exec:
	popl %eax                         /* return */
	movl $RSTACK_end,%ebp
	xchg %esp,%ebp
	pushl %eax
	xchg %esp,%ebp
	movl %ebp,%esi
	jmp EXECUTE

.global _start
_start:
	pushl $a12
	call forth_exec
	jmp _start

        .align 4,0
COREWORDS:
        .long 	corewords

        .bss
	.align 4,0
RSTACK:
	.fill 64,4,0
RSTACK_end:
