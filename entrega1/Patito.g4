// DESCRIPTION: Definicion de mi lenguaje PATITO

// Nombre 
grammar patito; //cambiar a Patito con mayuscula

//================================== TOKENS LEXICOS ==================================

// Ignora whitespace *agregado despues de entrega 0
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
RETURN     : 'return' ;   // lo agregue despues

// Simbolos y Operadores
ASSIGN : '=' ;
PLUS   : '+' ;
MINUS  : '-' ;
MUL    : '*' ;
DIV    : '/' ;
NEQ    : '!=' ;
LT     : '<' ;
GT     : '>' ;
EQ     : '==' ; // lo agregue despues
LEQ    : '<=' ; // lo agregue despues
GEQ    : '>=' ; // lo agregue despues
COMMA  : ',' ;
COLON  : ':' ;
SEMI   : ';' ;
LP     : '(' ;
RP     : ')' ;
LB     : '{' ;
RB     : '}' ;
LBR    : '[' ;
RBR    : ']' ;

// Tokens Lexicos (literales menos id) (los que defini en la etapa 0)

// Identificadores
ID : [A-Za-z_] [A-Za-z0-9_]* ;

// Enteros 
INT_LIT : '0' | [1-9] [0-9]* ;

// Flotantes
FLOAT_LIT : ([0-9]+ '.' [0-9]* | [0-9]* '.' [0-9]+) (EXPONENT)? ; 
fragment EXPONENT : [eE] [+-]? [0-9]+ ;

// Strings 
STRING_LIT : '"' ( ESC | ~["\\] )* '"' ;
fragment ESC : '\\' . ;

//================================== REGLAS DEL PARSER ==================================

// Entrada para el parser //EOF = End of file
start : programa EOF ;

// ----------------- <PROGRAMA> ------------------

programa : PROGRAM ID SEMI programa_p programa_pp MAIN body END ;
// PROGRAMA → program id ; PROGRAMA_PP PROGRAMA_PP main BODY end

programa_p : vars programa_p| /* empty */ ;
// PROGRAMA_P→ VARS PROGRAMA_P
// PROGRAMA_P→ ε

programa_pp : programa_ppp | /* empty */ ;
// PROGRAMA_PP → PROGRAMA_PPP
// PROGRAMA_PP → ε

programa_ppp : funcs programa_ppp | /* empty */ ;
// PROGRAMA_PPP→ FUNCS PROGRAMA_PPP
// PROGRAMA_PPP→ ε

// ----------------- <VARS> ------------------

vars : VAR vars_p ;
// VARS→ var VARS_P

vars_p : ID vars_pp COLON type SEMI ;
// VARS_P→ id VARS_PP : TYPE ; 

vars_pp : COMMA ID vars_pp | /* empty */ ;
// VARS_PP → , id VARS_PP
// VARS_PP → ε


// ----------------- <BODY> ------------------

body : LB body_p RB ;
//BODY → { BODY_P }

body_p : body_pp | /* empty */ ;
//BODY_P→ BODY_PP
//BODY_P→ ε

body_pp : statement body_pp | /* empty */ ;
//BODY_PP→ STATEMENT BODY_PP
//BODY_PP→ ε

// ----------------- <ASSIGN> ------------------

assign : ID ASSIGN expresion SEMI ;
// ASSIGN→ id = EXPRESION ;

// ----------------- <CYCLE> ------------------

cycle : WHILE LP expresion RP DO body SEMI ;
// CYCLE→ while ( EXPRESION ) do CUERPO ;

// ----------------- <TYPE> ------------------

type : INT_TYPE | FLOAT_TYPE ;
//TYPE → int
//TYPE → float

// ----------------- <CTE> ------------------

cte : INT_LIT | FLOAT_LIT ;
// CTE→ CTE_INT // cambie el nombre a que matchearan con mis tokens lexicos
// CTE→ CTE_FLOAT

// ----------------- <EXP> -----------------

exp : termino exp_p ;
// EXP→ TERMINO EXP_P

exp_p : PLUS termino exp_p | MINUS termino exp_p | /* empty */ ;
// EXP_P → + TERMINO EXP_P 
// EXP_P  → - TERMINO EXP_P 
// EXP_P  → ε

// ----------------- <TERMINO> ------------------

termino : factor termino_p ;
// TERMINO→ FACTOR TERMINO_P

termino_p : MUL factor termino_p | DIV factor termino_p | /* empty */ ;
// TERMINO_P → * FACTOR TERMINO_P
// TERMINO_P → / FACTOR TERMINO_P
// TERMINO_P → ε

// ----------------- <F_CALL> ------------------

fcall : ID LP fcall_p RP ;
// F_CALL→ id ( F_CALL_P ) 

fcall_p : expresion fcall_pp | /* empty */ ;
// F_CALL_P → EXPRESION F_CALL_PP
// F_CALL_P →ε

fcall_pp : COMMA fcall_p | /* empty */ ;
// F_CALL_PP → , F_CALL_P
// F_CALL_PP → ε // hise esta gramatica asi porque en la grafica se ciclaba despues de expresion, no habia salida. 

// ----------------- <STATEMENT> ------------------

statement : assign | condition | cycle | fcall SEMI | print_cfg | LB statement_p RB ;
// STATEMENT→ ASSIGN
// STATEMENT→ CONDITION
// STATEMENT→ CYCLE
// STATEMENT→ F_CALL ;
// STATEMENT→ PRINT
// STATEMENT → [ STATEMENT_P ]

statement_p : statement statement_p | /* empty */ ;
// STATEMENT_P→ STATEMENT STATEMENT_P
// STATEMENT_P→ ε

// ----------------- <CONDITION> ------------------

condition : IF LP expresion RP body condition_p SEMI ;
// CONDITION→ if ( EXPRESION ) BODY CONDITION_P ;

condition_p : ELSE body | /* empty */ ;
// CONDITION_P→ else BODY
// CONDITION_P→ε

// ----------------- <EXPRESION> ------------------

expresion : exp expresion_p ;
//EXPRESION → EXP EXPRESION_P

expresion_p : GT exp | LT exp | NEQ exp | EQ exp | GEQ exp | LEQ exp | /* empty */ ;
// EXPRESION_P→ > EXP
// EXPRESION_P→ < EXP
// EXPRESION_P→ != EXP
// EXPRESION_P→ == EXP
// EXPRESION_P→ ε
// Agregue tambien <= y >=

// ----------------- <FUNCS> ------------------
funcs : funcs_p ID LP funcs_pp RP LB funcs_ppp body RB SEMI ;
// FUNCS→ FUNCS_P id ( FUNCS_PP ) { FUNCS_PPP BODY } ;

funcs_p : VOID  | type ;
// FUNCS_P→ void
// FUNCS_P→ TYPE

funcs_pp : ID COLON type funcs_pppp | /* empty */;
// FUNCS_PP→ id : TYPE FUNCS_PPPP
// FUNCS_PP→ ε

funcs_ppp : vars | /* empty */ ;
// FUNCS_PPP→ VARS
// FUNCS_PPP→ε

funcs_pppp : COMMA funcs_pp | /* empty */ ;
// FUNCS_PPPP → , FUNCS_PP
// FUNCS_PPPP → ε

// ----------------- <FACTOR> ------------------

factor : LP expresion RP | factor_p | fcall ;
// FACTOR → ( EXPRESION )
// FACTOR → LLAMADA
// FACTOR → FACTOR_P

factor_p : factor_pp factor_ppp ;
// FACTOR_P → FACTOR_PP FACTOR_PPP

factor_pp : PLUS | MINUS | /* empty */ ;
// FACTOR_PP→ + 
// FACTOR_PP→ -
// FACTOR_PP→ ε

factor_ppp : ID | cte ;
// FACTOR_PPP→ id
// FACTOR_PPP→ CTE

// ----------------- <PRINT> ------------------

print_cfg : PRINT LP print_p print_pp RP SEMI ; 
// PRINT → print ( PRINT_P PRINT_PP ) ;

//lo nombre print_cfg porque ya usamos PRINT y print en los tokens

print_p : expresion print_pp | STRING_LIT print_pp ;
// PRINT_P→ EXPRESION PRINT_PP
// PRINT_P→ CTE_STRING PRINT_PP //STRING_LIT envez de CTE_STRING para que coincida con mis tokens

print_pp : COMMA print_p | /* empty */ ;
// PRINT_PP→ , PRINT_P
// PRINT_PP→ ε

// ----------------- <RETURN> ------------------
return_cfg : RETURN return_p SEMI ;

return_p : expresion | /* empty */ ;