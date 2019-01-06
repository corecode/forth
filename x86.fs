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

: WORD, ( addr len -- )
  DUP C,
  0 DO ( addr )
    DUP C@ C,
    1+
  LOOP
  DROP ( )
;

: CODE, ( xt -- )
  232 C, \ 232 = 0xE8 = call relative
  HERE 4 + -
  , \ xt
;

CODE doCREATE
	/* return address = DFA is already on stack */
	NEXT
END-CODE

: CREATE, ( -- nlink )
  ALIGN HERE ( nlink )
  LAST @ , ( nlink H: next )
  PARSE WORD, ALIGN ( H: next | name )
;

: CREATE
  CREATE,
  ['] doCREATE CODE,
  POSTPONE EXIT
;

CODE ,
	popl %eax
	movl UP_data,%ebx
        movl %eax,(%ebx)
	addl $4,UP_data
	NEXT
END-CODE

CODE C,
	popl %eax
	movl UP_data,%ebx
        movb %al,(%ebx)
        incl UP_data
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
      UNLOOP 2DROP 0 EXIT
    THEN
  LOOP
  2DROP 1
;

: ALIGNED ( addr -- addr )
  1 CELLS 1- ( addr 3 )
  DUP INVERT ( addr 3 ~3 )
  SWAP ROT ( ~3 3 addr )
  + AND
;

: ALIGN
  HERE ALIGNED UP !
;

: XT> ( addr -- xt )
  1 CELLS + ( cstr )
  DUP C@ 127 AND + 1+ ALIGNED
;

: FIND ( addr len -- addr len 0 | xt 1 | xt -1 )
  2DUP ( addr len addr len )
  LAST >R ( R: addr2 )
  BEGIN
    R> @ DUP >R ( addr len addr len addr2 )
  WHILE
    R@ 1 CELLS + ( addr len addr len c-addr2 )
    CMPWORD IF ( addr len )
      2DROP R> DUP ( addr addr ) ( R: )
      XT> SWAP ( xt addr )
      1 CELLS + ( xt c-addr )
      C@ ( xt len+flags )
      128 AND IF 1 ELSE -1 THEN ( xt -1 | xt 1 )
      EXIT
    THEN
    2DUP ( addr len addr len )
  REPEAT
  RDROP 2DROP 0 ( addr len 0 ) ( R: )
;

: DOES>
  \ XXX wrong
  R> ( xt )
  HERE 1 CELLS - ! ( overwrite jump address )
;

: :
  CREATE,
  ['] ENTER CODE,
  ]
;

: CELLS ( n -- n ) 4 * ;
: ALLOT ( n -- ) UP +! ;

: VARIABLE
  CREATE 1 CELLS ALLOT ,
;

VARIABLE UP
VARIABLE LAST
VARIABLE STATE
: [ 0 STATE ! ; IMMEDIATE
: ] 1 STATE ! ;
: HERE UP @ ;

: ; ( xt -- )
  POSTPONE EXIT
  LAST !
  POSTPONE [
; IMMEDIATE


CODE 0BRANCH
	lodsl
	popl %ebx
	testl %ebx,%ebx
	jnz .L1f
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
  POSTPONE 0BRANCH ,
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

: LEAVE ( R: loopend idx lim ret )
  RDROP RDROP RDROP ( R: loopend )
  \ now returns to loopend
;

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

: (+LOOP) ( n -- / R: loopend idx lim ret )
  R> SWAP ( ret n )
  R> R> ( ret n lim idx / R: loopend )
  ROT + ( ret lim newidx )
  2DUP >R >R ( ret lim idx R: loopend idx lim )
  = ( ret f )
  SWAP >R ( f / R: loopend idx lim ret )
;

: I ( -- n / R: idx lim )
  2 RPICK
;

: UNLOOP
  R> RDROP RDROP RDROP >R
;

: ' PARSE FIND DROP ;
: ['] PARSE FIND LITERAL ; IMMEDIATE

: LITERAL POSTPONE (LITERAL) , ;

: POSTPONE
  PARSE FIND 0 >
  IF COMPILE,
  ELSE LITERAL POSTPONE COMPILE, THEN
; IMMEDIATE

: PARSE-CH
  >R
  BEGIN SOURCELEN @ ( len )
        >IN @ SWAP < ( f )
  WHILE SOURCEBUF @ ( addr )
        >IN @ + C@ ( ch )
        R@ EXECUTE ( f )
  WHILE
    1 >IN +!
  REPEAT
  THEN \ close second WHILE
  RDROP
;

: IS-WS? 33 < ;
: NOT-WS? IS-WS? INVERT ;

: PARSE ( -- addr len )
  ['] IS-WS? PARSE-CH
  SOURCE DROP >IN @ DUP >R + ( addr R: startpos )
  ['] NOT-WS? PARSE-CH
  >IN @ R> ( addr endpos startpos )
  - ( addr len )
;

: EVALUATE ( source n -- )
  SOURCELEN ! SOURCEBUF !
  0 >IN !
  BEGIN >IN @ SOURCELEN @ < WHILE
    PARSE ( addr len )
    FIND DUP IF ( xt 1 | xt -1 )
      0 < STATE @ AND IF ( xt )
        COMPILE,
      ELSE
        EXECUTE
      THEN
    ELSE ( addr len 0 )
      DROP >NUMBER
      STATE @ IF
        LITERAL
      THEN
    THEN
  REPEAT
;

: >NUMBER ( addr len -- n )
  0 SWAP ( addr 0 len )
  0 DO ( addr sum )
    10 * SWAP ( sum addr )
    DUP 1+ SWAP ( sum addrnext addr )
    C@ 48 - ( sum addr n )
    ROT + ( addr sum )
  LOOP
  SWAP DROP
;

VARIABLE >IN
VARIABLE SOURCEBUF
VARIABLE SOURCELEN

: SOURCE SOURCEBUF @ SOURCELEN @ ;
