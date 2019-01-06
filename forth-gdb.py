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

    def thread_name(self, addr):
        word = self.thread_address(addr)
        if not word:
            return None
        return self.word_name(word)

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

f = Forthx86()
RStack(f)
