# Puntos neuralgicos
# entrega2/semantic_visitor.py

from __future__ import annotations

from entrega2.symbols import FunctionDirectory
from entrega2.semantic_cube import TypeName

from entrega1.generated.PatitoParser import PatitoParser
from entrega1.generated.PatitoVisitor import PatitoVisitor


class SemanticVisitor(PatitoVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.func_dir = FunctionDirectory() # Directorio de funciones y variables globales (tabla global)
        self.current_function: str | None = None # Contexto, none = global, si no es el nombre de la funcion actual

    # ----------------- Helpers internos ----------------- #

    #Declara una variable en el scope correcto (global o local)
    def _declare_var(self, name: str, type_: TypeName):
        if self.current_function is None:
            return self.func_dir.declare_global(name, type_)
        else:
            return self.func_dir.declare_local(self.current_function, name, type_)

    # ----------------- Reglas de programa/vars/funcs ----------------- #

    # start : programa EOF ;
    def visitStart(self, ctx: PatitoParser.StartContext):
        # delega en programa y regresa el directorio
        self.visit(ctx.programa())
        return self.func_dir

    # programa : PROGRAM ID SEMI programa_p programa_pp MAIN body END ;
    def visitPrograma(self, ctx: PatitoParser.ProgramaContext):
        prog_name = ctx.ID().getText()
        self.current_function = None #no se declara programa funcion, solo usamos scope global
        self.visit(ctx.programa_p()) # Global VARS
        self.visit(ctx.programa_pp()) # Funciones
        self.visit(ctx.body()) # MAIN body
        self.current_function = None #seguimos en scope global
        return self.func_dir

    # programa_p : vars programa_p | /* empty */ ;
    def visitPrograma_p(self, ctx: PatitoParser.Programa_pContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.vars_()) #mismo que vars (lo usa python)
        self.visit(ctx.programa_p())
        return None

    # programa_pp : programa_ppp | /* empty */ ;
    def visitPrograma_pp(self, ctx: PatitoParser.Programa_ppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.programa_ppp())
        return None

    # programa_ppp : funcs programa_ppp | /* empty */ ;
    def visitPrograma_ppp(self, ctx: PatitoParser.Programa_pppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.funcs())
        self.visit(ctx.programa_ppp())
        return None

    # ----------------- Tipos ----------------- #

    # type : INT_TYPE | FLOAT_TYPE ;
    # Solo regresamos int o float porque asi lo defini en la gramatica
    def visitType(self, ctx: PatitoParser.TypeContext) -> TypeName:
        if ctx.INT_TYPE():
            return "int"
        if ctx.FLOAT_TYPE():
            return "float"
        raise ValueError("Tipo no reconocido en regla 'type'")

    # ----------------- Declaracion de variables ----------------- #

    # vars   : VAR vars_p ;
    def visitVars(self, ctx: PatitoParser.VarsContext):
        return self.visit(ctx.vars_p())

    # vars_p : ID vars_pp COLON type SEMI ;
    def visitVars_p(self, ctx: PatitoParser.Vars_pContext):
        first_id = ctx.ID().getText()
        extra_ids = self.visit(ctx.vars_pp()) or []
        ids = [first_id] + extra_ids
        tname: TypeName = self.visit(ctx.type_()) #igual que type

        # Declara todas las variables de esa linea en el scope actual
        for name in ids:
            self._declare_var(name, tname)
        return None

    # vars_pp : COMMA ID vars_pp | /* empty */ ;
    def visitVars_pp(self, ctx: PatitoParser.Vars_ppContext):
        if ctx.getChildCount() == 0:
            return []
        this_id = ctx.ID().getText()
        rest = self.visit(ctx.vars_pp()) or []
        return [this_id] + rest

    # ----------------- Declaracion de funciones ----------------- #

    # funcs : funcs_p ID LP funcs_pp RP LB funcs_ppp body RB SEMI ;
    def visitFuncs(self, ctx: PatitoParser.FuncsContext):
        return_type: TypeName = self.visit(ctx.funcs_p()) #tipo de return, void, int o float
        func_name = ctx.ID().getText()
        self.func_dir.declare_function(func_name, return_type=return_type) #declara la funcion en el directorio
        prev_func = self.current_function #se cambia el contexto a scope local de la funcion
        self.current_function = func_name
        self.visit(ctx.funcs_pp()) #parametros
        self.visit(ctx.funcs_ppp()) #variables locales
        self.visit(ctx.body()) #body
        self.current_function = prev_func #restaurar el contexto anterior
        return None

    # funcs_p : VOID | type ;
    def visitFuncs_p(self, ctx: PatitoParser.Funcs_pContext) -> TypeName:
        if ctx.VOID():
            return "void"
        else:
            return self.visit(ctx.type_()) #igual que type

    # funcs_pp : ID COLON type funcs_pppp | /* empty */ ;
    def visitFuncs_pp(self, ctx: PatitoParser.Funcs_ppContext):
        if ctx.getChildCount() == 0:
            return None
        if self.current_function is None:
            raise RuntimeError("Parámetro declarado fuera de función")
        param_name = ctx.ID().getText()
        param_type: TypeName = self.visit(ctx.type_()) #igual que type
        self.func_dir.declare_param(self.current_function, param_name, param_type) #deckara parametro en la funcion actual
        self.visit(ctx.funcs_pppp()) #posibles parametros adicionales
        return None

    # funcs_pppp : COMMA funcs_pp | /* empty */ ;
    def visitFuncs_pppp(self, ctx: PatitoParser.Funcs_ppppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.funcs_pp())
        return None

    # funcs_ppp : vars | /* empty */ ;
    def visitFuncs_ppp(self, ctx: PatitoParser.Funcs_pppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.vars_()) #igual que vars
        return None
