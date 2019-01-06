ASFLAGS+=-32 -g --gen-debug
CFLAGS+=-m32 -g
LDFLAGS+=-m32 -g

# -acghlmns

all: assemble forth-x86

forth-x86: main.o forth-x86.o
	$(LINK.o) -o $@ $^

assemble: forth-x86.o

print: forth-x86.o
	cat forth-x86.s
	objdump -rsd $^
clean:
	-rm -f forth-x86.s forth-x86.o forth-x86 main.o

forth-x86.s: forth-asm.py x86.s x86.fs
	python forth-asm.py > $@
