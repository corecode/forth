import gdb
import itertools

class Forthx86:
    def __init__(self):
        self.i = gdb.selected_inferior()
        self.voidpp = gdb.lookup_type('void').pointer().pointer()
        self.ulong = gdb.lookup_type('unsigned long')
        self.charp = gdb.lookup_type('unsigned char').pointer()
        self.last = gdb.parse_and_eval('&LAST_data').cast(self.voidpp)
        self.rstack_end = gdb.parse_and_eval('&RSTACK_end')

    def read_next(self, val):
        return val.dereference().cast(self.voidpp)

    def iter_words(self):
        p = self.last.dereference().cast(self.voidpp)
        while p != 0:
            yield p.cast(self.ulong)
            p = p.dereference().cast(self.voidpp)

    def thread_address(self, addr):
        addr = gdb.Value(addr).cast(self.ulong)
        best = None
        for waddr in self.iter_words():
            if addr >= waddr and (not best or addr - waddr < addr - best):
                best = waddr
        return best

    def word_name(self, wordlink):
        lenp = gdb.Value(wordlink + 4).cast(self.charp)
        lenv = lenp.dereference() & 0x7f
        strp = lenp+1
        strv = self.i.read_memory(strp, lenv).tobytes().decode('utf-8')
        return strv

    def word_address(self, wordlink):
        lenp = gdb.Value(wordlink + 4).cast(self.charp)
        lenv = lenp.dereference() & 0x7f
        codep = wordlink + 4 + 1 + lenv
        codep = (codep + 3) / 4 * 4
        codep = gdb.Value(codep).cast(self.ulong)
        return codep

    def word_is_immediate(self, wordlink):
        lenp = gdb.Value(wordlink + 4).cast(self.charp)
        lenv = lenp.dereference()
        return lenv & 0x80 != 0

    def thread_name(self, addr):
        word = self.thread_address(addr)
        if not word:
            return None
        return self.word_name(word)

    def find(self, name):
        for word in self.iter_words():
            if name == self.word_name(word):
                return word

class RStack(gdb.Command):
    """Print FORTH return stack"""

    def __init__(self, forth):
        self.forth = forth
        super().__init__('rstack', gdb.COMMAND_STACK)

    def invoke(self, arg, from_tty):
        f = gdb.newest_frame()
        code = f.read_register('eip')
        print('%#x' % code, self.forth.thread_name(code), '\t(CODE)')
        caller = f.read_register('esp').cast(self.forth.voidpp).dereference()
        caller_name = self.forth.thread_name(caller)
        if caller_name == 'ENTER':
            print('%#x' % caller, caller_name, '\t(WORD)')
        ip = f.read_register('esi')
        print('%#x' % ip, self.forth.thread_name(ip), '\t(THREAD)')

        rstack = f.read_register('ebp').cast(self.forth.voidpp)
        for i in itertools.count():
            if (rstack[i].address >= self.forth.rstack_end):
                break
            print('%#x' % rstack[i], self.forth.thread_name(rstack[i]), '\t(RSTACK)')

class ForthSee(gdb.Command):
    """Print FORTH word"""

    def __init__(self, forth):
        self.forth = forth
        super().__init__('forthsee', gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        name = args[0]

        word = self.forth.find(name)
        if word is None:
            print('word `%s\' not found' % name)
            return

        addr = self.forth.word_address(word)
        print('word `%s\' at %#x' % (name, addr))

        entry_rel = gdb.Value(addr+1).cast(self.forth.voidpp).dereference()
        entry = entry_rel + addr - 4
        entry_name = self.forth.thread_name(entry)

        if entry_name == 'ENTER':
            addr += 5
            words = ''
            while True:
                elem = gdb.Value(addr).cast(self.forth.voidpp).dereference()
                elem_xt = self.forth.thread_address(elem)
                elem_name = self.forth.word_name(elem_xt)
                if elem_name == 'EXIT':
                    break
                if elem_name == '(LITERAL)':
                    addr += 4
                    val = gdb.Value(addr).cast(self.forth.voidpp).dereference()
                    val = val.cast(self.forth.ulong)
                    words += ' %d' % val
                else:
                    offset = elem - self.forth.word_address(elem_xt)
                    if offset == 0:
                        words += ' %s' % elem_name
                    else:
                        words += ' [%s+%d]' % (elem_name, offset)
                addr += 4
            immediate = ' IMMEDIATE' if self.forth.word_is_immediate(word) else ''
            print(': %s%s ;%s' % (self.forth.word_name(word), words, immediate))
        elif entry_name == 'doCREATE':
            print('VARIABLE %s' % self.forth.word_name(word))
        else:
            print('CODE %s' % self.forth.word_name(word))
        return

        f = gdb.newest_frame()
        code = f.read_register('eip')
        print('%#x' % code, self.forth.thread_name(code), '\t(CODE)')
        caller = f.read_register('esp').cast(self.forth.voidpp).dereference()
        caller_name = self.forth.thread_name(caller)
        if caller_name == 'ENTER':
            print('%#x' % caller, caller_name, '\t(WORD)')
        ip = f.read_register('esi')
        print('%#x' % ip, self.forth.thread_name(ip), '\t(THREAD)')

        rstack = f.read_register('ebp').cast(self.forth.voidpp)
        for i in itertools.count():
            if (rstack[i].address >= self.forth.rstack_end):
                break
            print('%#x' % rstack[i], self.forth.thread_name(rstack[i]), '\t(RSTACK)')

f = Forthx86()
RStack(f)
ForthSee(f)
