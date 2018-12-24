class Word:
    def __init__(self, name):
        self.name = name
        self.immediate = False
        self.data = []

    def execute(self, forth):
        for xt in self.data:
            forth.execute(xt)

    def __repr__(self):
        return "WORD(%s, %s)" % (self.name, ' '.join([str(xt) for xt in self.data]))

class Literal:
    def __init__(self, val):
        self.val = val

    def execute(self, forth):
        forth.push(self.val)

    def __repr__(self):
        return "LITERAL(%d)" % self.val

class Primitive:
    def __init__(self, name, f, immediate=False):
        self.name = name
        self.f = f
        self.immediate = immediate

    def execute(self, forth):
        self.f(forth)

    def __repr__(self):
        return "PRIMITIVE(%s)" % (self.name)

class Forth:
    def __init__(self):
        self.dict = {}
        self.stack = []
        self.rstack = []
        self.last = None
        self.state = False

        self.prim('+', lambda f: f.push(f.pop() + f.pop()))
        self.prim(':', Forth.colon)
        self.prim(';', Forth.semicolon, immediate=True)

    def prim(self, name, f, immediate=False):
        self.dict[name] = Primitive(name, f, immediate)

    def find(self, w):
        return self.dict[w]

    def colon(self):
        self.last = Word(self.word())
        self.state = True

    def semicolon(self):
        self.state = False
        self.dict[self.last.name] = self.last

    def comma(self, t):
        self.last.data.append(t)

    def push(self, val):
        self.stack.append(val)

    def pop(self):
        return self.stack.pop()

    def execute(self, xt):
        xt.execute(self)

    def eval(self, s):
        self.input = s
        self.inputpos = 0
        self.loop()

    def loop(self):
        while self.inputpos < len(self.input):
            self.eval_one()

    def word(self):
        while self.inputpos < len(self.input) and self.input[self.inputpos].isspace():
            self.inputpos += 1
        w = ""
        while self.inputpos < len(self.input) and not self.input[self.inputpos].isspace():
            w += self.input[self.inputpos]
            self.inputpos += 1
        return w

    def eval_one(self):
        w = self.word()
        try:
            xt = self.find(w)
            if not self.state or xt.immediate:
                self.execute(xt)
            else:
                self.comma(xt)
        except KeyError:
            val = int(w)
            if not self.state:
                self.push(val)
            else:
                self.comma(Literal(val))

    def dump(self):
        print("Input:")
        print(self.input)
        print(" "*self.inputpos + "^")
        print("Stack:")
        for v in self.stack:
            print(v)
        print("Word list:")
        for k,v in self.dict.items():
            print("%s = %s%s" % (k, v, " IMMEDIATE" if v.immediate else ""))

def test(s):
    f = Forth()
    try:
        f.eval(s)
    finally:
        f.dump()

if __name__ == "__main__":
    test("1 2 +")
    test(": a12 1 2 + ; a12")
