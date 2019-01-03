import io
import re
import binascii

class ForthAsm:
    def __init__(self, output):
        self.output = output
        self.wordlist = []
        self.commands = {
            ':': self.cmd_COLON,
            ';': self.cmd_SEMICOLON,
            'CODE': self.cmd_CODE,
            '(': self.cmd_PAREN,
            '\\': self.cmd_BACKSLASH,
            'IMMEDIATE': self.cmd_IMMEDIATE,
            'VARIABLE': self.cmd_VARIABLE,
        }
        self.start()

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
        if not hasattr(f, 'read'):
            f = io.StringIO(f)
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

    def cmd_PAREN(self):
        while True:
            w = self.word()
            if w == "" or w == ")":
                break

    def cmd_BACKSLASH(self):
        while True:
            ch = self.input.read(1)
            if ch == '\n' or ch == "":
                break

    def cmd_COLON(self):
        w = self.word()
        self.wordlist.append(w)
        self.header(w)
        self.enter()

    def cmd_SEMICOLON(self):
        self.exit()

    def cmd_CODE(self):
        w = self.word()
        self.wordlist.append(w)
        self.header(w)
        self.assemble()

    def assemble(self):
        code = ""
        ch = ""
        while True:
            ws = ch
            w = ""
            while True:
                ch = self.input.read(1)
                if ch == "":
                    return
                if ch.isspace():
                    if w != "":
                        break
                    ws += ch
                else:
                    w += ch

            if w == "END-CODE":
                break

            code += ws
            code += w

        self.code(code)

    def cmd_IMMEDIATE(self):
        self.immediate()

    def cmd_VARIABLE(self):
        w = self.word()
        self.wordlist.append(w)
        self.header(w)
        self.variable(w)

class Forth_x86(ForthAsm):
    def quote(self, w):
        w = re.sub(r'\W', lambda s: "."+binascii.hexlify(s[0].encode("utf-8")).decode('ascii')+".", w)
        if w[0].isdigit():
            w = '.'+w
        return w

    def start(self):
        self.headers = []
        self.immediates = {}

        self.output.write(open('x86.s').read())
        self.parse(open('x86.fs'))

    def end(self):
        self.output.write("\n")
        for name in self.wordlist:
            fields = {
                'sym': self.quote(name),
                'len': len(name) | (0x80 if name in self.immediates else 0),
            }
            self.output.write("""\
	.set %(sym)s_len, %(len)d
""" % fields)

        self.output.write("\n")
        last = "0"
        for h in reversed(self.headers):

            self.output.write("""\
	.set .L%s_next, %s
""" % (h, last))
            last = h+"_link"
        self.output.write("""\
	.set corewords, %s
""" % last)

    def header(self, name):
        fields = {
            'sym': self.quote(name),
            'len': len(name),
            'name': name,
        }
        self.headers.append(fields['sym'])
        self.output.write("""
	.text
	.align 4,0
%(sym)s_link:
	.long .L%(sym)s_next
	.byte %(sym)s_len
	.ascii "%(name)s"
	.align 4,0
%(sym)s:
""" % fields)

    def immediate(self):
        name = self.wordlist[-1]
        self.immediates[name] = True

    def code(self, code):
        self.output.write(code)
        self.output.write("\n")

    def enter(self):
        self.output.write("""\
	call ENTER
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
        self.reference('(LITERAL)')
        self.output.write("""\
	.long %d
""" % val)

    def variable(self, name):
        sym = self.quote(name)
        self.output.write("""
	pushl $%(sym)s_data
	NEXT

.data
%(sym)s_data:
	.long 0
""" % {'sym': sym} )

if __name__ == "__main__":
    import sys
    import io
    f = Forth_x86(sys.stdout)
    f.end()
