class ForthAsm:
    def __init__(self, output):
        self.output = output
        self.wordlist = {}
        self.commands = {
            ':': self.cmd_COLON,
            ';': self.cmd_SEMICOLON,
        }
        self.start()

    def quote(self, w):
        replace = {
            '+': '_PLUS',
        }
        for k,v in replace.items():
            w = w.replace(k, v)
        return w

    def word(self):
        while True:
            ch = self.input.read(1)
            if ch == "":
                return ""
            if ch.isspace():
                continue
            else:
                result = ch
                break

        while True:
            ch = self.input.read(1)
            if ch == "" or ch.isspace():
                break
            else:
                result += ch

        return result

    def parse(self, f):
        self.input = f
        while self.eval():
            pass

    def eval(self):
        w = self.word()
        if w == "":
            return False
        if w in self.commands:
            self.commands[w]()
        else:
            try:
                v = int(w)
                self.literal(v)
            except ValueError:
                self.reference(w)
        return True

    def cmd_COLON(self):
        w = self.word()
        self.wordlist[w] = True
        self.header(w)
        self.doCOLON()

    def cmd_SEMICOLON(self):
        self.exit()

class Forth_x86(ForthAsm):
    def start(self):
        self.headers = []

        self.output.write("""\
		.text
.macro NEXT
		lodsl
		jmp *%eax
.endm

doCOLON:
		xchgl %esp,%ebp
		pushl %esi
		xchgl %esp,%ebp
		popl %esi
		NEXT

EXIT:
		xchgl %esp,%ebp
		popl %esi
		xchgl %esp,%ebp
		NEXT

_LITERAL:
		lodsl
		pushl %eax
		NEXT

_PLUS:
		popl %eax
		popl %ebx
		addl %ebx,%eax
		pushl %eax
		NEXT

EXECUTE:
		popl %eax
		jmp *%eax

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

		.data
		.align 4,0
RSTACK:
		.fill 64,4,0
RSTACK_end:
""")

    def end(self):
        self.output.write("\n")
        last = "0"
        for h in reversed(self.headers):
            self.output.write("""\
		.set %s_next, %s
""" % (h, last))
            last = h+"_link"
        self.output.write("""
		.data
WORDLIST:
		.long %s
""" % last)

    def header(self, name, immediate=False):
        fields = {
            'sym': self.quote(name),
            'len': len(name) | (0x80 if immediate else 0),
            'name': name,
        }
        self.headers.append(fields['sym'])
        self.output.write("""
		.text
		.align 4,0
%(sym)s_link:
		.long %(sym)s_next
		.byte %(len)d
		.ascii "%(name)s"
		.align 4,0
%(sym)s:
""" % fields)

    def doCOLON(self):
        self.output.write("""\
		call doCOLON
""")

    def exit(self):
        self.output.write("""\
		.long EXIT
""")

    def reference(self, word):
        self.output.write("""\
		.long %s
""" % self.quote(word))

    def literal(self, val):
        self.reference('_LITERAL')
        self.output.write("""\
		.long %d
""" % val)

if __name__ == "__main__":
    import sys
    import io
    f = Forth_x86(sys.stdout)
    f.parse(io.StringIO(": a2 2 + ; : a12 1 a2 ;"))
    f.end()
    #f.header("test")
