CODE doCOLON
	xchgl %esp,%ebp
	pushl %esi
	xchgl %esp,%ebp
	popl %esi
	NEXT
END-CODE

CODE +
	popl %eax
	addl %eax,(%esp)
	NEXT
END-CODE

CODE EXIT
	xchgl %esp,%ebp
	popl %esi
	xchgl %esp,%ebp
	NEXT
END-CODE

CODE (LITERAL)
	lodsl
	pushl %eax
	NEXT
END-CODE

CODE EXECUTE
	popl %eax
	jmp *%eax
END-CODE
