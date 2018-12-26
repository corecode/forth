ASFLAGS=-32 -acghlmns

all: assemble print

assemble: forth-x86.o

print: forth-x86.o
	objdump -rsd $^
clean:
	-rm -f forth-x86.s forth-x86.o

forth-x86.s: forth-asm.py x86.s x86.fs
	python forth-asm.py > $@
	cat $@
