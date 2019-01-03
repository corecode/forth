(
IP - esi
PSP - esp
RSP - ebp
W - eax
)

CODE DUP
	pushl (%esp)
        NEXT
END-CODE

CODE 2DUP
	pushl 4(%esp)
	pushl 4(%esp)
        NEXT
END-CODE

CODE DROP
	popl %eax
        NEXT
END-CODE

CODE 2DROP
	leal 8(%esp),%esp
        NEXT
END-CODE

CODE RDROP
	leal 4(%ebp),%ebp
	NEXT
END-CODE

CODE SWAP
	popl %eax
        popl %ebx
        pushl %eax
        pushl %ebx
        NEXT
END-CODE

CODE ROT
	movl (%esp),%eax
        movl 4(%esp),%ebx
        movl %eax,4(%esp)
        movl 8(%esp),%eax
        movl %ebx,8(%esp)
        movl %eax,(%esp)
	NEXT
END-CODE

CODE R>
	pushl (%ebp)
	leal 4(%ebp),%ebp
        NEXT
END-CODE

CODE >R
	leal -4(%ebp),%ebp
        popl (%ebp)
        NEXT
END-CODE

CODE R@
	pushl (%ebp)
	NEXT
END-CODE

CODE RPICK
	popl %eax
	pushl (%ebp,%eax,4)
	NEXT
END-CODE

CODE @
	popl %eax
	pushl (%eax)
	NEXT
END-CODE

CODE C@
	popl %eax
        movzbl (%eax),%eax
	pushl %eax
	NEXT
END-CODE

CODE !
	popl %edi
	popl %eax
	stosl
        NEXT
END-CODE

CODE +
	popl %eax
	addl %eax,(%esp)
	NEXT
END-CODE

CODE -
	popl %eax
	subl %eax,(%esp)
        NEXT
END-CODE

CODE 1-
	decl (%esp)
        NEXT
END-CODE

CODE 1+
	incl (%esp)
        NEXT
END-CODE

CODE +!
	popl %ebx
	popl %eax
	addl %eax,(%ebx)
	NEXT
END-CODE

CODE *
	popl %eax
	popl %ecx
	mull %ecx
        pushl %eax
        NEXT
END-CODE

: COMPILE, , ;

CODE AND
	popl %eax
	andl %eax,(%esp)
	NEXT
END-CODE

CODE OR
	popl %eax
	orl %eax,(%esp)
	NEXT
END-CODE

CODE INVERT
	notl (%esp)
        NEXT
END-CODE

CODE =
	popl %eax
        subl %ebx,%ebx
        cmpl %eax,(%esp)
	setneb %bl
        decl %ebx
        movl %ebx,(%esp)
        NEXT
END-CODE

CODE 0=
	popl %eax
	subl %ebx,%ebx
        orl %eax,%eax
	setneb %bl
        decl %ebx
        movl %ebx,(%esp)
        NEXT
END-CODE

CODE >
	popl %eax
        subl %ebx,%ebx
        cmpl %eax,(%esp)
	setleb %bl
        decl %ebx
        movl %ebx,(%esp)
        NEXT
END-CODE

CODE <
	popl %eax
        subl %ebx,%ebx
        cmpl %eax,(%esp)
	setgeb %bl
        decl %ebx
        movl %ebx,(%esp)
        NEXT
END-CODE

CODE ENTER
	xchgl %esp,%ebp
	pushl %esi
	xchgl %esp,%ebp
	popl %esi
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

: WORD,
  DUP C@ ( c-addr len )
  -1 SWAP ( c-addr -1 len )
  DO ( c-addr )
    DUP C@ C,
    1+
  LOOP
;

: CODE, ( xt -- )
  232 C, \ 232 = 0xE8 = call
  , \ xt
;

CODE doCREATE
	/* return address = DFA is already on stack */
	NEXT
END-CODE

: CREATE
  ALIGN HERE ( nlink )
  LAST @ , ( nlink H: next )
  PARSE WORD,
  ALIGN HERE ( nlink xt )
  ' doCREATE CODE,
  POSTPONE EXIT
;

CODE ,
	popl %eax
	movl UP,%ebx
        movl %eax,(%ebx)
	addl $4,UP
	NEXT
END-CODE

CODE C,
	popl %eax
	movl UP,%ebx
        movb %al,(%ebx)
        incl UP
        NEXT
END-CODE

: CMPWORD ( addr len waddr -- f )
  DUP C@ 127 AND ( addr len waddr len2 )
  ROT DUP >R ( addr waddr len2 len / R: len )
  - IF ( addr waddr )
    RDROP 2DROP 0 EXIT ( 0 / R: )
  THEN
  1+ ( addr1 addr2 )
  R> 0 DO
    2DUP I + C@ ( addr1 addr2 addr1 c2 )
    SWAP I + C@ ( addr1 addr2 c2 c1 )
    - IF ( addr1 addr2 )
      UNLOOP 2DROP 0 LEAVE
    THEN
  LOOP
  2DROP 1
;

: ALIGNED ( addr -- addr )
  1 CELLS + 1- 1 CELLS INVERT AND
;

: ALIGN
  HERE ALIGNED UP !
;

: XT> ( addr -- xt )
  DUP C@ 127 AND + ALIGNED
;

: FIND ( addr len -- addr len 0 | xt 1 | xt -1 )
  2DUP ( addr len addr len )
  LAST >R ( R: addr2 )
  BEGIN
    R> @ DUP >R ( addr len addr len addr2 )
  WHILE
    R@ 1 CELLS + ( addr len addr len c-addr2 )
    CMPWORD IF ( addr len )
      2DROP R> DUP XT> SWAP 1 CELLS + C@ ( xt len+flags ) ( R: )
      DUP 128 AND IF 1 ELSE -1 THEN ( xt -1 | xt 1 )
      EXIT
    THEN
    2DUP
  REPEAT
  R> 2DROP 0 ( addr len 0 ) ( R: )
;

: DOES>
  R> ( xt )
  HERE 1 CELLS - !
; IMMEDIATE

: : CREATE ]

;

: CELLS ( n -- n ) 4 * ;
: ALLOT ( n -- ) DP +! ;

: VARIABLE
  CREATE 1 CELLS ALLOT ,
;

: HERE DP @ ;

VARIABLE DP
VARIABLE STATE

: ; ( xt -- )
  LAST !
  [
; IMMEDIATE

: [ STATE 1 ! ; IMMEDIATE
: ] STATE 0 ! ;

CODE 0BRANCH
	lodsl
	popl %ebx
	testl %ebx,%ebx
	jz .L1f
        movl %eax,%esi
.L1f:
	NEXT
END-CODE

CODE BRANCH
	lodsl
	movl %eax,%esi
        NEXT
END-CODE

: IF ( -- orig )
  POSTPONE 0BRANCH
  HERE
  0 ,
; IMMEDIATE

: THEN ( orig -- )
  HERE SWAP !
; IMMEDIATE

: BEGIN ( -- dest )
  HERE
; IMMEDIATE

: AGAIN ( dest -- )
  POSTPONE BRANCH ,
; IMMEDIATE

: UNTIL ( dest -- )
  POSTPONE 0= POSTPONE 0BRANCH ,
; IMMEDIATE

: AHEAD ( -- orig )
  POSTPONE BRANCH
  HERE
  0 ,
; IMMEDIATE

: ELSE ( orig1 -- orig2 )
  POSTPONE AHEAD ( orig1 orig2 )
  SWAP ( orig2 orig1 )
  POSTPONE THEN
; IMMEDIATE

: WHILE ( dest -- orig dest )
  POSTPONE IF ( dest orig )
  SWAP ( orig dest )
; IMMEDIATE

: REPEAT ( orig dest -- )
  POSTPONE AGAIN ( orig )
  POSTPONE THEN ( )
; IMMEDIATE

: DO ( -- 0 orig / exe: lim idx -- )
  POSTPONE >R POSTPONE >R
  0 ( mark end of references )
  POSTPONE BEGIN
; IMMEDIATE

: LEAVE ( 0 orig1 -- 0 orig2 orig1 )
  >R POSTPONE AHEAD >R
; IMMEDIATE

: LOOP POSTPONE 1 POSTPONE +LOOP ; IMMEDIATE

: +LOOP ( 0 origN orig2 orig1 -- )
  POSTPONE (+LOOP)
  POSTPONE UNTIL ( 0 origN orig2 )
  BEGIN DUP WHILE
    POSTPONE THEN
  REPEAT ( 0 )
  DROP
  POSTPONE UNLOOP
; IMMEDIATE

: (+LOOP) ( n -- / R: idx lim )
  R> R> ROT + ( lim nidx R: )
  2DUP >R >R ( lim idx R: idx lim )
  = ( f )
;

: I ( -- n / R: idx lim )
  1 RPICK
;

: UNLOOP
  RDROP RDROP
;

: ' PARSE FIND DROP ; IMMEDIATE
: ['] PARSE FIND LITERAL ; IMMEDIATE

: LITERAL POSTPONE (LITERAL) , ;

: POSTPONE
  PARSE FIND 0 >
  IF COMPILE,
  ELSE LITERAL POSTPONE COMPILE, THEN
; IMMEDIATE

: PARSE-CH
  >R
  BEGIN SOURCE >IN @ >
        >IN @ + C@
        R@ EXECUTE AND WHILE
    >IN 1 +!
  REPEAT
  RDROP
;

: IS-WS? 33 < ;
: NOT-WS? IS-WS? INVERT ;

: PARSE ( -- addr len )
  ['] IS-WS? PARSE-CH
  SOURCE DROP >IN @ DUP >R - ( addr R: startpos )
  ['] NOT-WS? PARSE-CH
  >IN @ R> SWAP ( addr endpos startpos )
  - ( addr len )
;

: EVALUATE ( source n -- )
  SOURCELEN ! SOURCEBUF !
  0 >IN !
  BEGIN >IN @ SOURCELEN @ < WHILE
    PARSE 2DUP ( addr len )
    FIND DUP IF ( xt 1 | xt -1 )
      0 > STATE @ OR IF ( xt )
        EXECUTE
      ELSE
        COMPILE,
      THEN
    ELSE ( addr len 0 )
      DROP >NUMBER
    THEN
  REPEAT
;

: >NUMBER ( addr len -- n )
  SWAP >R ( len / R: addr )
  0 SWAP ( 0 len )
  0 DO ( n )
    10 *
    R@ I + C@ 48 - +
  LOOP
  RDROP
;

VARIABLE >IN
VARIABLE SOURCEBUF
VARIABLE SOURCELEN

: SOURCE SOURCEBUF SOURCELEN ;

VARIABLE UP
VARIABLE LAST
