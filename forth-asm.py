import io
import re
import binascii

class ForthAsm:
    def __init__(self, output):
        self.output = output
        self.wordlist = []
        self.immediates = []
        self.referenced = set()
        self.ctrl_stack = []
        self.commands = {
            ':': self.cmd_COLON,
            ';': self.cmd_SEMICOLON,
            'CODE': self.cmd_CODE,
            '(': self.cmd_PAREN,
            '\\': self.cmd_BACKSLASH,
            'IMMEDIATE': self.cmd_IMMEDIATE,
            'VARIABLE': self.cmd_VARIABLE,
            'POSTPONE': self.cmd_POSTPONE,
            'BEGIN': self.cmd_BEGIN,
            'WHILE': self.cmd_WHILE,
            'IF': self.cmd_IF,
            'THEN': self.cmd_THEN,
            'AGAIN': self.cmd_AGAIN,
            'REPEAT': self.cmd_REPEAT,
            'ELSE': self.cmd_ELSE,
            'AHEAD': self.cmd_AHEAD,
            'DO': self.cmd_DO,
            'LOOP': self.cmd_LOOP,
            '+LOOP': self.cmd_PLUS_LOOP,
            'UNTIL': self.cmd_UNTIL,
            '[\']': self.cmd_BRACKET_TICK,
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
                self.literal(w)
                return True
            except ValueError:
                pass

            if w in self.immediates:
                raise RuntimeError("Implement %s in meta-compiler" % w) from None
            self.referenced.add(w)
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
        self.state = 1
        self.enter()

    def cmd_SEMICOLON(self):
        self.exit()
        self.state = 0

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
        w = self.wordlist[-1]
        if w in self.referenced:
            raise RuntimeError("implement %s in the meta-compiler" % w)
        self.immediates.append(w)
        self.immediate()

    def cmd_VARIABLE(self):
        w = self.word()
        self.wordlist.append(w)
        self.header(w)
        self.variable(w)

    def cmd_POSTPONE(self):
        w = self.word()
        if w in self.immediates:
            self.reference(w)
        else:
            self.literal(w)
            self.reference('COMPILE,')

    def cmd_BEGIN(self):
        self.rec_jmp_dest()

    def cmd_WHILE(self):
        self.cmd_IF()
        self.cs_roll(1)

    def cs_roll(self, n):
        t = self.ctrl_stack[-n-1:]
        t2 = t[n:] + t[:n]
        self.ctrl_stack[-n-1:] = t2

    def cmd_IF(self):
        self.reference('0BRANCH')
        self.rec_jmp_orig()

    def cmd_AGAIN(self):
        self.reference('BRANCH')
        self.res_jmp_dest()

    def cmd_THEN(self):
        self.res_jmp_orig()

    def cmd_REPEAT(self):
        self.cmd_AGAIN()
        self.cmd_THEN()

    def cmd_ELSE(self):
        self.cmd_AHEAD()
        self.cs_roll(1)
        self.cmd_THEN()

    def cmd_AHEAD(self):
        self.reference('BRANCH')
        self.rec_jmp_orig()

    def cmd_DO(self):
        self.reference('(LITERAL)')
        self.rec_jmp_orig()
        self.reference('>R')

        self.reference('>R')
        self.reference('>R')
        self.cmd_BEGIN()

    def cmd_LOOP(self):
        self.literal(1)
        self.cmd_PLUS_LOOP()

    def cmd_PLUS_LOOP(self):
        self.reference('(+LOOP)')
        self.cmd_UNTIL()
        self.reference('UNLOOP')
        self.cmd_THEN()

    def cmd_UNTIL(self):
        self.reference('0BRANCH')
        self.res_jmp_dest()

    def cmd_BRACKET_TICK(self):
        w = self.word()
        self.literal(w)


class Forth_x86(ForthAsm):
    def quote(self, w):
        w = re.sub(r'\W', lambda s: "."+binascii.hexlify(s[0].encode("utf-8")).decode('ascii')+".", w)
        if w[0].isdigit():
            w = '.'+w
        return w

    def start(self):
        self.headers = []
        self.ctrl_pos = 0

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
        try:
            int(val)
            val = str(val)
        except ValueError:
            val = self.quote(val)

        self.output.write("""\
	.long %s
""" % val)

    def variable(self, name):
        sym = self.quote(name)
        self.output.write("""
	pushl $%(sym)s_data
	NEXT

.data
%(sym)s_data:
	.long 0
""" % {'name': name, 'sym': sym} )

    def rec_jmp_dest(self):
        self.output.write("""\
.Lb%d:
""" % self.ctrl_pos)
        self.ctrl_stack.append(self.ctrl_pos)
        self.ctrl_pos += 1

    def res_jmp_dest(self):
        self.output.write("""\
	.long .Lb%(dest)d
""" % {'dest': self.ctrl_stack.pop()})

    def rec_jmp_orig(self):
        self.output.write("""\
	.long .Lb%(pos)d_dest
""" % {'pos': self.ctrl_pos})
        self.ctrl_stack.append(self.ctrl_pos)
        self.ctrl_pos += 1

    def res_jmp_orig(self):
        self.output.write("""\
.Lb%(orig)d_dest:
""" % {'orig': self.ctrl_stack.pop()})


if __name__ == "__main__":
    import sys
    import io
    f = Forth_x86(sys.stdout)
    f.end()
