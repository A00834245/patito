# Generated from src/patito/Patito.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PatitoParser import PatitoParser
else:
    from PatitoParser import PatitoParser

# This class defines a complete generic visitor for a parse tree produced by PatitoParser.

class PatitoVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PatitoParser#start.
    def visitStart(self, ctx:PatitoParser.StartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#programa.
    def visitPrograma(self, ctx:PatitoParser.ProgramaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#programa_p.
    def visitPrograma_p(self, ctx:PatitoParser.Programa_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#programa_pp.
    def visitPrograma_pp(self, ctx:PatitoParser.Programa_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#programa_ppp.
    def visitPrograma_ppp(self, ctx:PatitoParser.Programa_pppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#vars.
    def visitVars(self, ctx:PatitoParser.VarsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#vars_p.
    def visitVars_p(self, ctx:PatitoParser.Vars_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#vars_pp.
    def visitVars_pp(self, ctx:PatitoParser.Vars_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#vars_ppp.
    def visitVars_ppp(self, ctx:PatitoParser.Vars_pppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#funcs.
    def visitFuncs(self, ctx:PatitoParser.FuncsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#funcs_p.
    def visitFuncs_p(self, ctx:PatitoParser.Funcs_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#funcs_pp.
    def visitFuncs_pp(self, ctx:PatitoParser.Funcs_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#funcs_ppp.
    def visitFuncs_ppp(self, ctx:PatitoParser.Funcs_pppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#funcs_pppp.
    def visitFuncs_pppp(self, ctx:PatitoParser.Funcs_ppppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#body.
    def visitBody(self, ctx:PatitoParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#body_p.
    def visitBody_p(self, ctx:PatitoParser.Body_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#body_pp.
    def visitBody_pp(self, ctx:PatitoParser.Body_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#condition.
    def visitCondition(self, ctx:PatitoParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#condition_p.
    def visitCondition_p(self, ctx:PatitoParser.Condition_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#exp.
    def visitExp(self, ctx:PatitoParser.ExpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#exp_p.
    def visitExp_p(self, ctx:PatitoParser.Exp_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#termino.
    def visitTermino(self, ctx:PatitoParser.TerminoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#termino_p.
    def visitTermino_p(self, ctx:PatitoParser.Termino_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#factor.
    def visitFactor(self, ctx:PatitoParser.FactorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#factor_p.
    def visitFactor_p(self, ctx:PatitoParser.Factor_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#factor_pp.
    def visitFactor_pp(self, ctx:PatitoParser.Factor_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#factor_ppp.
    def visitFactor_ppp(self, ctx:PatitoParser.Factor_pppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#expresion.
    def visitExpresion(self, ctx:PatitoParser.ExpresionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#expresion_p.
    def visitExpresion_p(self, ctx:PatitoParser.Expresion_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#print_stmt.
    def visitPrint_stmt(self, ctx:PatitoParser.Print_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#print_p.
    def visitPrint_p(self, ctx:PatitoParser.Print_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#print_pp.
    def visitPrint_pp(self, ctx:PatitoParser.Print_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#fcall.
    def visitFcall(self, ctx:PatitoParser.FcallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#fcall_p.
    def visitFcall_p(self, ctx:PatitoParser.Fcall_pContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#fcall_pp.
    def visitFcall_pp(self, ctx:PatitoParser.Fcall_ppContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#statement.
    def visitStatement(self, ctx:PatitoParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#assign.
    def visitAssign(self, ctx:PatitoParser.AssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#type.
    def visitType(self, ctx:PatitoParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#cte.
    def visitCte(self, ctx:PatitoParser.CteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PatitoParser#cycle.
    def visitCycle(self, ctx:PatitoParser.CycleContext):
        return self.visitChildren(ctx)



del PatitoParser