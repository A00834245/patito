grammar Patito;

// ---------- LEXICO ----------

// Ignora whitespace
WS : [ \t\r\n]+ -> skip ;

// Palabras reservadas
PROGRAM    : 'program' ;
MAIN       : 'main' ;
END        : 'end' ;
IF         : 'if' ;
ELSE       : 'else' ;
WHILE      : 'while' ;
DO         : 'do' ;
PRINT      : 'print' ;
VAR        : 'var' ;
VOID       : 'void' ;
INT_TYPE   : 'int' ;
FLOAT_TYPE : 'float' ;

// Simbolos y Operadores
ASSIGN : '=' ;
PLUS   : '+' ;
MINUS  : '-' ;
MUL    : '*' ;
DIV    : '/' ;
NEQ    : '!=' ;
LT     : '<' ;
GT     : '>' ;
COMMA  : ',' ;
COLON  : ':' ;
SEMI   : ';' ;
LP     : '(' ;
RP     : ')' ;
LB     : '{' ;
RB     : '}' ;
LBR    : '[' ;
RBR    : ']' ;

// Tokens Lexicos

// Identificadores
ID : [A-Za-z_] [A-Za-z0-9_]* ;

// Enteros decimales
INT_LIT : '0' | [1-9] [0-9]* ;

// Flotantes
FLOAT_LIT
 : [0-9]+ '.' [0-9]+ (EXP)?   // 12.34, 12.34e+5
 ;

// Strings 
STRING_LIT
 : '"' ( ESC | ~["\\] )* '"'
 ;


// ---------- FRAGMENTS ----------

fragment EXP : [eE] [+-]? [0-9]+ ;
fragment ESC : '\\' . ;


// ---------- RULES (CFG) ----------
// NOTA: Las reglas primas (EXP') las cambie a p (EXP_P) para que sea ANTLR friendly. 

// Punto de entrada
start
 : programa EOF
 ;

// ***** <Programa> (PROGRAMA, PROGRAMA_P, PROGRAMA_PP, Programa_PPP)
programa
: PROGRAM ID SEMI programa_p programa_pp MAIN body END
;

programa_p
: vars
| /* empty */
;

programa_pp
: programa_ppp
| /* empty */
;

programa_ppp
: funcs programa_ppp
| /* empty */
;

// ***** <VARS> (VARS, VARS_P, VARS_PP, VARS_PPP)
vars
: VAR vars_p
;

vars_p
: ID vars_pp COLON type SEMI vars_ppp
;

vars_pp
: COMMA ID vars_pp
| /* empty */
;

vars_ppp
: vars_p
| /* empty */
;


// ***** <FUNCS> (FUNCS, FUNCS_P, FUNCS_PP, FUNCS_PPP, FUNCS_PPPP)
funcs
: VOID ID LP funcs_p RP LBR funcs_pppp body RBR SEMI
;

funcs_p
: funcs_pp
| /* empty */
;

funcs_pp
: ID COLON type funcs_ppp
;

funcs_ppp
: COMMA funcs_pp
| /* empty */
;

funcs_pppp
: vars
| /* empty */
;

// ***** <BODY> (BODY, BODY_P, BODY_PP)
body
: LB body_p RB
;

body_p
: body_pp
| /* empty */
;

body_pp
: statement body_pp
| /* empty */
;

// ***** <CONDITION> (CONDITION, CONDITION_P)
condition
 : IF LP expresion RP body condition_p SEMI
 ;

condition_p
 : ELSE body
 | /* empty */
 ;

// ***** <EXP> (EXP, EXP_P)
exp
 : termino exp_p
 ;

exp_p
 : PLUS termino exp_p
 | MINUS termino exp_p
 | /* empty */
 ;


// ***** <TERMINO> (TERMINO, TERMINO_P)
termino
 : factor termino_p
 ;

termino_p
 : MUL factor termino_p
 | DIV factor termino_p
 | /* empty */
 ;

// ***** <FACTOR> (FACTOR, FACTOR_P)
factor
 : LP expresion RP
 | factor_p
 ;

factor_p
 : factor_pp factor_ppp
 ;

factor_pp
 : PLUS
 | MINUS
 | /* empty */
 ;

factor_ppp
 : ID
 | cte
 ;

// ***** <EXPRESION> (EXPRESION, EXPRESION_P)
expresion
 : exp expresion_p
 ;

expresion_p
 : GT exp
 | LT exp
 | NEQ exp
 | /* empty */
 ;

// ***** <PRINT> (PRINT, PRINT_P)
print_stmt
 : PRINT LP print_p print_pp RP SEMI
 ;

print_p
 : expresion print_pp
 | STRING_LIT print_pp
 ;

print_pp
 : COMMA print_p
 | /* empty */
 ;

// ***** <FCALL> (FCALL_PP, FCALL_P)
fcall
 : ID LP fcall_p RP SEMI
 ;

fcall_p
 : expresion fcall_pp
 | /* empty */
 ;

fcall_pp
 : COMMA fcall_p
 | /* empty */
 ;

// ***** <STATEMENT> 
statement
: assign
| condition
| cycle
| fcall
| print_stmt
;

// ***** <ASSIGN> 
assign
 : ID ASSIGN expresion SEMI
 ;


// ***** <TYPE> 
type
 : INT_TYPE
 | FLOAT_TYPE
 ;

// ***** <CTE> 
cte
 : INT_LIT
 | FLOAT_LIT
 ;

// ***** <CYCLE> 
cycle
 : WHILE LP expresion RP DO body SEMI
 ;







