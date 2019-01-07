import io
import re
import binascii

class ForthAsm:
    def __init__(self, output):
        self.output = output
        self.wordlist = []
        self.words = {}
        self.immediates = []
        self.referenced = set()
        self.stack = []
        self.state = 0
        self.immediate_commands = {
            ';': self.cmd_SEMICOLON,
            'CODE': self.cmd_CODE,
            '(': self.cmd_PAREN,
            '\\': self.cmd_BACKSLASH,
            'IMMEDIATE': self.cmd_IMMEDIATE,
            'VARIABLE': self.cmd_VARIABLE,
            'POSTPONE': self.cmd_POSTPONE,
            '[\']': self.cmd_BRACKET_TICK,
        }
        self.commands = {
            ':': self.cmd_COLON,
            'ALIGN': self.cmd_ALIGN,
            'HERE': self.cmd_HERE,
            'SWAP': self.cmd_SWAP,
            '!': self.cmd_STORE,
            ',': self.cmd_COMMA,
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
        try:
            while self.eval():
                pass
        except Exception as e:
            raise RuntimeError("near %s" % self.wordlist[-1]) from e


    def eval(self):
        w = self.word()
        if w == "":
            return False
        if w in self.immediate_commands:
            self.immediate_commands[w]()
        else:
            try:
                v = int(w)
                if self.state:
                    self.literal(w)
                else:
                    self.push(w)
                return True
            except ValueError:
                pass

            if self.state and not w in self.immediates:
                if not w in self.wordlist:
                    raise RuntimeError("unknown word %s" % w)
                self.referenced.add(w)
                self.compile_comma(w)
            else:
                self.execute(w)

        return True

    def compile_comma(self, w):
        self.words[self.wordlist[-1]].append(w)
        self.reference(w)

    def execute(self, w):
        if w in self.immediate_commands:
            self.comment("IMMEDATE %s" % w)
            self.immediate_commands[w]()
        elif w in self.commands:
            self.comment("META-WORD %s" % w)
            self.commands[w]()
        else:
            self.comment("WORD %s" % w)

            thread = list(self.words[w])
            while len(thread) > 0:
                c = thread.pop(0)
                if c == '(LITERAL)':
                    v = thread.pop(0)
                    self.push(v)
                else:
                    try:
                        self.execute(c)
                    except Exception as e:
                        raise RuntimeError("in %s" % w) from e

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
        self.words[w] = []
        self.state = 1
        self.enter()

    def cmd_SEMICOLON(self):
        self.exit()
        self.state = 0
        self.comment(": %s %s ;" % (self.wordlist[-1],
                                    ' '.join(self.words[self.wordlist[-1]])))

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
        # if w in self.referenced:
        #     raise RuntimeError("implement %s in the meta-compiler" % w)
        self.immediates.append(w)
        self.immediate()

    def cmd_VARIABLE(self):
        w = self.word()
        self.wordlist.append(w)
        self.header(w)
        self.variable(w)

    def cmd_POSTPONE(self):
        w = self.word()
        self.comment("POSTPONE %s" % w)
        if w in self.immediates:
            self.compile_comma(w)
        elif w in self.wordlist:
            self.literal(w)
            self.compile_comma('COMPILE,')
        else:
            raise RuntimeError("unknown word %s" % w)

    def cmd_BRACKET_TICK(self):
        w = self.word()
        self.literal(w)

    def cmd_ALIGN(self):
        self.align()

    def cmd_HERE(self):
        self.push(self.here())

    def cmd_SWAP(self):
        self.stack[-2],self.stack[-1] = self.stack[-1],self.stack[-2]
        self.comment("STACK [ %s ]" % ' '.join([str(e) for e in self.stack]))

    def cmd_STORE(self):
        addr = self.pop()
        val = self.pop()
        self.store(addr, val)

    def cmd_COMMA(self):
        val = self.pop()
        self.comma(val)

    def push(self, v):
        self.stack.append(v)
        self.comment("STACK [ %s ]" % ' '.join([str(e) for e in self.stack]))

    def pop(self):
        v = self.stack.pop()
        self.comment("STACK [ %s ]" % ' '.join([str(e) for e in self.stack]))
        return v

class Forth_x86(ForthAsm):
    def comment(self, args):
        self.output.write("/* %s */\n" % args)

    def quote(self, w):
        w = re.sub(r'\W', lambda s: "."+binascii.hexlify(s[0].encode("utf-8")).decode('ascii')+".", w)
        if w[0].isdigit():
            w = '.'+w
        return w

    def start(self):
        self.vals = {}
        self.headers = []
        self.hereloc = 0
        self.here_valid = None
        self.output.write(open('x86.s').read())
        self.parse(open('x86.fs'))

    def end(self):
        self.output.write("\n")
        for a,v in self.vals.items():
            self.output.write("""\
	.set %s,%s
""" % (a, v))

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
        self.writehere()
        self.output.write("""\
	call ENTER
""")

    def exit(self):
        self.writehere()
        self.output.write("""\
	.long EXIT
""")

    def reference(self, word):
        self.writehere()
        try:
            s = str(int(word))
        except:
            s = self.quote(word)
        if word[:3] == ".Lh":
            s = word
        self.output.write("""\
	.long %s
""" % s)

    def literal(self, val):
        self.compile_comma('(LITERAL)')
        self.compile_comma(val)
#         try:
#             int(val)
#             val = str(val)
#         except ValueError:
#             val = self.quote(val)

#         self.output.write("""\
# 	.long %s
# """ % val)

    def variable(self, name):
        sym = self.quote(name)
        self.output.write("""
	pushl $%(sym)s_data
	NEXT

.data
%(sym)s_data:
	.long 0
""" % {'name': name, 'sym': sym} )

    def align(self):
        self.writehere()
        self.output.write("""\
	.align 4,0
""")

    def genhereloc(self):
        if self.here_valid:
            return self.here_valid
        self.hereloc += 1
        loc = '.Lh%d' % self.hereloc
        return loc

    def writehere(self):
        if self.here_valid:
            self.output.write("%s:\n" % self.here_valid)
            self.here_valid = None

    def here(self):
        loc = self.genhereloc()
        self.here_valid = loc
        return loc

    def store(self, addr, val):
        self.writehere()
        self.vals[addr] = val

    def comma(self, val):
        if not self.here_valid:
            self.reference(val)
        else:
            loc = self.here_valid
            self.output.write("""\
	.long %s
""" % loc)
            self.vals[loc] = val
            self.here_valid = None

if __name__ == "__main__":
    import sys
    import io
    f = Forth_x86(sys.stdout)
    f.end()
