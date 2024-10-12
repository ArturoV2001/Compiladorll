import tkinter as tk
from tkinter import END, Text, ttk
from tkinter import filedialog
import ply.lex as lex
import ply.yacc as yacc
import subprocess
from tkinter.filedialog import askopenfilename
import os
import graphviz
from PIL import Image, ImageTk

asm_code = ""
code = ""
if_code = ""  # Inicializar if_code
relacionales = []
labels = 1
labelsE = 1
lexerErrors = ""
in_if_context = False
primera = 0
imge_path = r'C:\Users\Artur\Desktop\COMPILADORES ll\proyecto v2.0\syntax_tree.png'
# Tabla hash para almacenar variables y sus tipos
table = {}


def print_tree(node):
    if isinstance(node, tuple):
        label = node[0]
        children = node[1:]
        dot.node(str(node), label)
        for child in children:
            if isinstance(child, tuple):
                child_label = child[0]
                child_node = str(child)
                dot.node(child_node, child_label)
                dot.edge(str(node), child_node)
                print_tree(child)
            else:
                child_node = str(child)
                dot.node(child_node, str(child))
                dot.edge(str(node), child_node)
    else:
        dot.node(str(node), str(node))


reserved = {
    'program': 'PROGRAM',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'fi': 'FI',
    'do': 'DO',
    'until': 'UNTIL',
    'for': 'FOR',
    'while': 'WHILE',
    'read': 'READ',
    'write': 'WRITE',
    'int': 'INT',
    'char': 'CHAR',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'not': 'NOT',
    'and': 'AND',
    'or': 'OR',
    'true': 'TRUE',
    'false': 'FALSE',
    'break': 'BREAK'
}

tokens = [
             'NUMBER',
             'PLUS',
             'MINUS',
             'TIMES',
             'DIVIDE',
             'LPAREN',
             'RPAREN',
             'EXPONENT',
             'DOUBLE',
             'ID',
             'EQUAL',
             'POINT',
             'RESERVED',
             'LEESTHAN',
             'MORETHAN',
             'OBRACKET',
             'CBRACKET',
             'SEMICOLON',
             'COLON',
             'MARK',
             'DOUBLEMARK',
             'MOREETHAN',
             'LEESETHAN',
             'EQUALEQUAL',
             'DIFFEQUAL',
             'COMA'
         ] + list(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_MARK = r'\''
t_DOUBLEMARK = r'\"'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EXPONENT = r'\^'
t_EQUAL = r'='
t_EQUALEQUAL = r'=='
t_DIFFEQUAL = r'!='
t_LEESTHAN = r'<'
t_MORETHAN = r'>'
t_LEESETHAN = r'<='
t_MOREETHAN = r'>='
t_OBRACKET = r'\{'
t_CBRACKET = r'\}'
t_SEMICOLON = r';'
t_COLON = r':'
t_COMA = r','


def t_DOUBLE(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# Agregar el token para los comentarios de bloque
def t_COMMENT_BLOCK(t):
    r'/\*([^*]|\*+[^*/])*\*+/'
    pass  # Ignorar el comentario


# Opcionalmente, agregar el token para comentarios de una sola línea
def t_COMMENT_LINE(t):
    r'//.*'
    pass  # Ignorar el comentario


t_ignore = ' \t'


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    print(t)
    errorBox.delete(1.0, END)
    errorBox.insert(1.0, "Illegal character '%s'" % t.value[0] + "at line: " + str(t.lineno) + "\n")
    archivo_salida = open("erroresLexer.txt", "a")
    # Escribir contenido en el archivo
    archivo_salida.write("Illegal character '%s'" % t.value[0] + "at line: " + str(t.lineno) + "\n")
    # Cerrar el archivo
    archivo_salida.close()
    t.lexer.skip(1)


# aqui va mis garamaticales yacc
def p_error(p):
    print("Error!!", p)
    errorBox.delete(1.0, END)
    errorBox.insert(1.0, "Error de semantica: " + str(p) + "\n")
    archivo_salida = open("erroresYacc.txt", "a")
    # Escribir contenido en el archivo
    archivo_salida.write("Error de semantica: " + str(p) + "\n")
    # Cerrar el archivo
    archivo_salida.close()


def p_program(p):
    '''program : PROGRAM OBRACKET statement_list CBRACKET
               | PROGRAM OBRACKET CBRACKET'''
    if len(p) == 4:
        p[0] = ('program', p[1])  # p[1] es PROGRAM, p[3] es CBRACKET
    else:
        p[0] = ('program', p[1], p[3])  # Para asegurar que la producción sea correcta


def p_statement_list(p):
    '''statement_list : statement 
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = ('statement_list', p[1])
    else:
        global asm_code, code, labels, primera
        if (primera <= 1):
            asm_code = asm_code + code
            primera = primera + 1
            code = ""
        else:
            asm_code = asm_code + ' goto L' + str(labels) + '\n'
            asm_code = asm_code + ' L' + str(labels + 1) + ': \n'
            asm_code = asm_code + code
            asm_code = asm_code + ' L' + str(labels) + ': \n'
            labels = labels + 2
            code = ""
        p[0] = ('statement_list', p[1], p[2])


def p_statement(p):
    '''statement : sent_assign
            |      write_statement
            |      var_declaration_statement
            |      if_statement
            |      iteration_statement
        '''
    p[0] = ('statement', p[1])


def p_do_while_statement(p):
    '''do_while_statement : DO OBRACKET statement_list CBRACKET UNTIL LPAREN sent_assign RPAREN'''
    p[0] = ('do_while_statement', p[1], p[3], p[5], p[7])


def p_for_statement(p):
    '''for_statement : FOR LPAREN sent_assign sent_assign RPAREN OBRACKET statement_list CBRACKET'''
    p[0] = ('for_statement', p[3], p[4], p[7])


def p_while_statement(p):
    '''while_statement : WHILE LPAREN sent_assign RPAREN OBRACKET statement_list CBRACKET'''
    p[0] = ('while_statement', p[3], p[6])
    global asm_code, code, if_code, labels, labelsE

    # Inicio del bucle
    asm_code += f'L{labels}: \n'
    start_label = labels
    labels += 1

    # Condición del bucle
    asm_code += 'if ('
    relacionales = if_code.split("ç")
    cond_code = [parte for parte in relacionales if parte]
    for parte in cond_code:
        asm_code += f'{parte} ) goto L{labels}\n'  # Si la condición se cumple, salta a la etiqueta de ejecución
    asm_code += f'goto E{labelsE}\n'  # Si no se cumple, salta al final del bucle
    exec_label = labels
    labels += 1

    # Contenido del bucle
    asm_code += f'L{exec_label}: \n'
    asm_code += code  # Instrucciones dentro del cuerpo del bucle

    # Aquí actualiza la tabla de símbolos
    if 'y' in table:
        variable_type, variable_name, variable_valor = table['y']
        table['y'] = (variable_type, variable_name, variable_valor - 1)

    asm_code += f'goto L{start_label}\n'  # Regresa al inicio del bucle

    # Fin del bucle
    asm_code += f'E{labelsE}: \n'
    labelsE += 1

    # Limpiar las variables globales
    if_code = ""
    relacionales = []
    code = ""


def p_iteration_statement(p):
    '''iteration_statement : for_statement
                           | while_statement
                           | do_while_statement '''
    p[0] = ('iteration_statement', p[1])


def p_if_statement(p):
    '''if_statement : IF LPAREN sent_assign RPAREN THEN OBRACKET statement_list CBRACKET FI
                    | IF LPAREN sent_assign RPAREN THEN OBRACKET statement_list CBRACKET ELSE OBRACKET statement_list CBRACKET FI'''
    global asm_code, code, if_code, relacionales, labels, labelsE
    if len(p) == 10:
        p[0] = ('if_statement', p[3], p[7])
        asm_code = asm_code + ' if ( '
        relacionales = relacionales[::-1]
        relacionales.append("ç")
        cadenas = if_code.split("ç")
        cadenas = [condicion for condicion in cadenas if condicion]
        for i, parte in enumerate(cadenas, 1):
            asm_code = asm_code + str(parte) + ' ' + ')' + 'goto L' + str(labels) + '\n'
            if (relacionales[i - 1] == 'and'):
                asm_code = asm_code + ' ' + 'goto E' + str(labelsE) + '\n'
                asm_code = asm_code + ' L' + str(labels) + ': if ( '
                labels = labels + 1
            elif (relacionales[i - 1] == 'or'):
                asm_code = asm_code + ' ' + 'goto L' + str(labels) + '\n'
                asm_code = asm_code + ' L' + str(labels) + ': if ( '
                labels = labels + 1
            else:
                asm_code = asm_code + ' ' + 'goto E' + str(labelsE) + '\n'
                asm_code = asm_code + ' E' + str(labelsE) + ':' + '\n'
                asm_code = asm_code + ' goto L' + str(labels + 1) + '\n'
                labelsE = labelsE + 1
                asm_code = asm_code + ' L' + str(labels) + ': ' + 'goto L' + str(labels + 3) + '\n'
                asm_code = asm_code + ' L' + str(labels + 1) + ': \n'
                labels = labels + 1
        relacionales = []
        if_code = ""
        labels = labels + 1
        relacionales = []
    else:
        p[0] = ('if_statement', p[3], p[7], p[11])
        asm_code = asm_code + ' if ( '
        relacionales = relacionales[::-1]
        relacionales.append("ç")
        cadenas = if_code.split("ç")
        cadenas = [condicion for condicion in cadenas if condicion]
        for i, parte in enumerate(cadenas, 1):
            asm_code = asm_code + str(parte) + ' ' + ')' + 'goto L' + str(labels) + '\n'
            if (relacionales[i - 1] == 'and'):
                asm_code = asm_code + ' ' + 'goto E' + str(labelsE) + '\n'
                asm_code = asm_code + ' L' + str(labels) + ': if ( '
                labels = labels + 1
            elif (relacionales[i - 1] == 'or'):
                asm_code = asm_code + ' ' + 'goto L' + str(labels) + '\n'
                asm_code = asm_code + ' L' + str(labels) + ': if ( '
                labels = labels + 1
            else:
                asm_code = asm_code + ' ' + 'goto E' + str(labelsE) + '\n'
                asm_code = asm_code + ' E' + str(labelsE) + ':' + '\n'
                asm_code = asm_code + ' goto L' + str(labels + 1) + '\n'
                labelsE = labelsE + 1
                asm_code = asm_code + ' L' + str(labels) + ': ' + 'goto L' + str(labels + 3) + '\n'
                asm_code = asm_code + ' L' + str(labels + 1) + ': \n'
                labels = labels + 1
        relacionales = []
        if_code = ""
        labels = labels + 1
        relacionales = []
    return asm_code, code, if_code, relacionales, labels, labelsE


def p_var_declaration_statement(p):
    '''var_declaration_statement : type_declaration var_list SEMICOLON
                                | ID var_list SEMICOLON'''
    global code
    if len(p) == 4 and p[1][0] == 'type_declaration':
        variable_type = p[1][1] if p[1][0] == 'type_declaration' else None
        if variable_type == 'bool':
            variable_valor = 'true'
        elif variable_type == 'int':
            variable_valor = 0  # asignar un valor predeterminado a las variables
        else:
            variable_valor = 0.0
        for variable_name in p[2][1]:
            if variable_name in table:
                entry3.insert(1.0, f'Error variable {variable_name} ya declarada \n')
            else:
                table[variable_name] = (variable_type, variable_name, variable_valor)
                code = code + ' ' + variable_type + ' ' + variable_name + '\n'
                code = code + ' ' + variable_name + ' = ' + str(variable_valor) + '\n'
        p[0] = ('VAR_DECLARATION', p[1], p[2][1])
    else:
        p[0] = ('VAR_DECLARATION', p[1], p[2][1])
    return code,


def p_var_list(p):
    '''var_list : ID
                | ID COMA var_list'''
    if len(p) == 2:
        # p[0] = p[1]
        p[0] = ('VAR_LIST', [p[1]])  # Si es solo un identificador, crea una lista con ese identificador
    else:
        # p[0] = [p[1]] + p[3]  # Si hay más identificadores, concaténalos a la lista existente
        p[0] = ('VAR_LIST', [p[1]] + p[3][1])


def p_type_declaration(p):
    '''type_declaration : INT 
                        | CHAR
                        | FLOAT
                        | BOOL'''
    p[0] = ('type_declaration', p[1])


def p_write_statement(p):
    '''write_statement : WRITE expr SEMICOLON'''
    global code
    valor = recorrer_arbol_retornar_ultimo(p[2])
    if valor in table:
        (variable_type, variable_name, variable_valor) = table[valor]
        table["write"] = ("float", "write", variable_valor)
        errorBox.insert(1.0, f'Write: {float(variable_valor)} \n')
    else:
        table["write"] = ("float", "write", float(valor))
        errorBox.insert(1.0, f'Write: {valor} \n')
    code = code + ' write ' + str(valor) + '\n'
    p[0] = ("write_statement", p[1], valor)
    return code


def p_sent_assign(p):
    '''sent_assign : ID EQUAL exp_bool SEMICOLON
                   | exp_bool SEMICOLON
                   | exp_bool'''
    global code
    if len(p) == 2:  # Caso 'exp_bool'
        segundo = recorrer_arbol_retornar_ultimo(p[1])
        if segundo == 'true' or segundo == 'false':
            # Solo si es booleano
            table['resultado'] = ('bool', 'resultado', segundo)
        else:
            entry3.insert(1.0, f'Error: expresión no booleana\n')
        p[0] = ("sent_assign", p[1])

    elif len(p) == 3:  # Caso 'exp_bool SEMICOLON'
        segundo = recorrer_arbol_retornar_ultimo(p[1])
        if segundo == 'true' or segundo == 'false':
            # Solo si es booleano
            table['resultado'] = ('bool', 'resultado', segundo)
        else:
            entry3.insert(1.0, f'Error: expresión no booleana\n')
        p[0] = ("sent_assign", p[1])

    else:  # Caso 'ID EQUAL exp_bool SEMICOLON'
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        if segundo == 'true' or segundo == 'false':
            if p[1] in table:
                variable_type, variable_name, variable_valor = table[p[1]]
                if variable_type == 'bool':
                    table[variable_name] = (variable_type, variable_name, segundo)
                    code += f'{variable_name} = {segundo}\n'
                else:
                    entry3.insert(1.0, f'Error de tipo: {variable_name} no es booleana\n')
            else:
                entry3.insert(1.0, f'Error: variable {p[1]} no declarada\n')
        else:
            entry3.insert(1.0, f'Error: asignación inválida {p[1]} = {segundo}\n')
        p[0] = ("sent_assign", p[1], p[3])

    return code


def p_exp_bool(p):
    '''exp_bool : exp_bool OR comb
                | comb'''
    if len(p) == 2:
        p[0] = ("exp_bool", p[1])  # El árbol de análisis sintáctico simplemente toma la comb directamente
    else:
        global relacionales
        primero = recorrer_arbol_retornar_ultimo(p[1])
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        boleano1 = 'false'
        boleano2 = 'false'
        boleano11 = False
        boleano22 = False
        relacionales.append("or")
        if (primero in table or primero == 'true' or primero == 'false') and (
                (segundo in table) or segundo == 'true' or segundo == 'false'):
            if primero == 'true' or primero == 'false':
                boleano1 = primero
            if segundo == 'true' or segundo == 'false':
                boleano2 = segundo
            if primero in table:
                (variable_type, variable_name, variable_valor) = table[primero]
                if variable_type == 'bool':
                    boleano1 = variable_valor
                else:
                    entry3.insert(1.0, f'Error en asignacion, variable {variable_name} no es boleana \n')
                    p[0] = ("exp_bool", p[2], p[1], p[
                        3])  # El árbol de análisis sintáctico tiene el operador lógico OR y las comb correspondientes
            if segundo in table:
                (variable_types, variable_names, variable_valors) = table[segundo]
                if variable_types == 'bool':
                    boleano2 = variable_valors
                else:
                    entry3.insert(1.0, f'Error en asignacion, variable {variable_names} no es boleana \n')
                    p[0] = ("exp_bool", p[2], p[1], p[
                        3])  # El árbol de análisis sintáctico tiene el operador lógico OR y las comb correspondientes
            if boleano1 == 'true':
                boleano11 = True
            else:
                boleano11 = False
            if boleano2 == 'true':
                boleano22 = True
            else:
                boleano22 = False
            if boleano11 or boleano22:
                p[0] = ("exp_bool", 'true')
            else:
                p[0] = ("exp_bool", 'false')
        elif primero in table or primero == 'true' or primero == 'false':
            entry3.insert(1.0, f'Error variable {segundo} no esta declarada en operacion or \n')
            p[0] = ("exp_bool", p[2], p[1],
                    p[3])  # El árbol de análisis sintáctico tiene el operador lógico OR y las comb correspondientes
        else:
            entry3.insert(1.0, f'Error {primero} no esta declarada en operacion or \n')
            p[0] = ("exp_bool", p[2], p[1],
                    p[3])  # El árbol de análisis sintáctico tiene el operador lógico OR y las comb correspondientes
        return relacionales


def p_comb(p):
    '''comb : comb AND igualdad
            | igualdad'''
    if len(p) == 2:
        p[0] = ("comb", p[1])  # El árbol de análisis sintáctico simplemente toma la igualdad directamente
    else:
        global relacionales
        boleano1 = 'false'
        boleano2 = 'false'
        boleano11 = False
        boleano22 = False
        primero = recorrer_arbol_retornar_ultimo(p[1])
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        relacionales.append("and")
        if (primero in table or primero == 'true' or primero == 'false') and (
                (segundo in table) or segundo == 'true' or segundo == 'false'):
            if primero == 'true' or primero == 'false':
                boleano1 = primero
            if segundo == 'true' or segundo == 'false':
                boleano2 = segundo
            if primero in table:
                (variable_type, variable_name, variable_valor) = table[primero]
                if variable_type == 'bool':
                    boleano1 = variable_valor
                else:
                    entry3.insert(1.0, f'Error en asignacion, variable {variable_name} no es boleana \n')
                    p[0] = ("comb", p[2], p[1], p[
                        3])  # El árbol de análisis sintáctico tiene el operador lógico AND y las igualdades correspondientes
            if segundo in table:
                (variable_types, variable_names, variable_valors) = table[segundo]
                if variable_types == 'bool':
                    boleano2 = variable_valors
                else:
                    entry3.insert(1.0, f'Error en asignacion, variable {variable_names} no es boleana \n')
                    p[0] = ("comb", p[2], p[1], p[
                        3])  # El árbol de análisis sintáctico tiene el operador lógico AND y las igualdades correspondientes
            if boleano1 == 'true':
                boleano11 = True
            else:
                boleano11 = False
            if boleano2 == 'true':
                boleano22 = True
            else:
                boleano22 = False
            if boleano11 and boleano22:
                p[0] = ("comb", 'true')
            else:
                p[0] = ("comb", 'false')
        elif primero in table or primero == 'true' or primero == 'false':
            entry3.insert(1.0, f'Error variable {segundo} no esta declarada en operacion and \n')
            p[0] = ("comb", p[2], p[1], p[
                3])  # El árbol de análisis sintáctico tiene el operador lógico AND y las igualdades correspondientes
        else:
            p[0] = ("comb", p[2], p[1], p[
                3])  # El árbol de análisis sintáctico tiene el operador lógico AND y las igualdades correspondientes
            entry3.insert(1.0, f'Error variable {primero} no esta declarada en operacion and\n')
        return relacionales


def p_igualdad(p):
    '''igualdad : igualdad EQUALEQUAL rel
                | igualdad DIFFEQUAL rel
                | rel'''
    if len(p) == 2:
        p[0] = ("igualdad", p[1])  # El árbol de análisis sintáctico simplemente toma el rel directamente
    else:
        global if_code
        boleano1 = 'false'
        boleano2 = 'false'
        boleano11 = False
        boleano22 = False
        boleano111 = 0
        boleano222 = 0
        bandera1 = 0
        bandera2 = 0
        if p[2] == '==':
            primero = recorrer_arbol_retornar_ultimo(p[1])
            segundo = recorrer_arbol_retornar_ultimo(p[3])
            if_code = if_code + ' ' + str(primero) + ' ' + '==' + ' ' + str(segundo) + 'ç'
            if (primero in table or primero == 'true' or primero == 'false' or isinstance(primero, int) or isinstance(
                    primero, float)) and (
                    (segundo in table) or segundo == 'true' or segundo == 'false' or isinstance(segundo,
                                                                                                int) or isinstance(
                    segundo, float)):
                if primero == 'true' or primero == 'false':
                    boleano1 = primero
                if segundo == 'true' or segundo == 'false':
                    boleano2 = segundo
                if primero in table:
                    (variable_type, variable_name, variable_valor) = table[primero]
                    if variable_type == 'bool':
                        boleano1 = variable_valor
                    elif variable_type == 'int' or variable_type == 'float':
                        bandera1 = 1
                        boleano111 = variable_valor
                    else:
                        entry3.insert(1.0,
                                      f'Error en asignacion, variable {variable_name} no se puede usar en operacion == \n')
                        p[0] = ("igualdad", p[2], p[1], p[3])
                if segundo in table:
                    (variable_types, variable_names, variable_valors) = table[segundo]
                    if variable_types == 'bool':
                        boleano2 = variable_valors
                    elif variable_types == 'int' or variable_types == 'float':
                        bandera2 = 1
                        boleano222 = variable_valors
                    else:
                        entry3.insert(1.0,
                                      f'Error en asignacion, variable {variable_names} no se puede usar en operacion == \n')
                        p[0] = ("igualdad", p[2], p[1], p[3])
                if isinstance(primero, int) or isinstance(primero, float):
                    bandera1 = 1
                    boleano111 = primero
                if isinstance(segundo, int) or isinstance(segundo, float):
                    bandera2 = 1
                    boleano222 = segundo
                if boleano1 == 'true':
                    boleano11 = True
                else:
                    boleano11 = False
                if boleano2 == 'true':
                    boleano22 = True
                else:
                    boleano22 = False
                if bandera1 == 1 and bandera2 == 1:
                    if boleano111 == boleano222:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                elif bandera1 == 1 and bandera2 != 1:
                    if boleano111 == boleano22:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                elif bandera1 != 1 and bandera2 == 1:
                    if boleano11 == boleano222:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                else:
                    if boleano11 == boleano22:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
            elif primero in table or primero == 'true' or primero == 'false':
                entry3.insert(1.0, f'Error variable {segundo} no esta declarada en la operacion == \n')
                p[0] = ("igualdad", p[2], p[1], p[3])
            else:
                entry3.insert(1.0, f'Error variable {primero} no esta declarada en la operacion == \n')
                p[0] = ("igualdad", p[2], p[1], p[3])
        else:
            primero = recorrer_arbol_retornar_ultimo(p[1])
            segundo = recorrer_arbol_retornar_ultimo(p[3])
            if_code = if_code + ' ' + str(primero) + ' ' + '!=' + ' ' + str(segundo) + ';'
            if (primero in table or primero == 'true' or primero == 'false' or isinstance(primero, int) or isinstance(
                    primero, float)) and (
                    (segundo in table) or segundo == 'true' or segundo == 'false' or isinstance(segundo,
                                                                                                int) or isinstance(
                    segundo, float)):
                if primero == 'true' or primero == 'false':
                    boleano1 = primero
                if segundo == 'true' or segundo == 'false':
                    boleano2 = segundo
                if primero in table:
                    (variable_type, variable_name, variable_valor) = table[primero]
                    if variable_type == 'bool':
                        boleano1 = variable_valor
                    elif variable_type == 'int' or variable_type == 'float':
                        bandera1 = 1
                        boleano111 = variable_valor
                    else:
                        entry3.insert(1.0,
                                      f'Error en asignacion, variable {variable_name} no se puede usar en operacion == \n')
                        p[0] = ("igualdad", p[2], p[1], p[3])
                if segundo in table:
                    (variable_types, variable_names, variable_valors) = table[segundo]
                    if variable_types == 'bool':
                        boleano2 = variable_valors
                    elif variable_types == 'int' or variable_types == 'float':
                        bandera2 = 1
                        boleano222 = variable_valors
                    else:
                        entry3.insert(1.0,
                                      f'Error en asignacion, variable {variable_names} no se puede usar en operacion == \n')
                        p[0] = ("igualdad", p[2], p[1], p[3])
                if isinstance(primero, int) or isinstance(primero, float):
                    bandera1 = 1
                    boleano111 = primero
                if isinstance(segundo, int) or isinstance(segundo, float):
                    bandera2 = 1
                    boleano222 = segundo
                if boleano1 == 'true':
                    boleano11 = True
                else:
                    boleano11 = False
                if boleano2 == 'true':
                    boleano22 = True
                else:
                    boleano22 = False
                if bandera1 == 1 and bandera2 == 1:
                    if boleano111 != boleano222:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                elif bandera1 == 1 and bandera2 != 1:
                    if boleano111 != boleano22:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                elif bandera1 != 1 and bandera2 == 1:
                    if boleano11 != boleano222:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
                else:
                    if boleano11 != boleano22:
                        p[0] = ("igualdad", 'true')
                    else:
                        p[0] = ("igualdad", 'false')
            elif primero in table or primero == 'true' or primero == 'false':
                entry3.insert(1.0, f'Error variable {segundo} no esta declarada en la operacion != \n')
                p[0] = ("igualdad", p[2], p[1], p[3])
            else:
                entry3.insert(1.0, f'Error variable {primero} no esta declarada en la operacion != \n')
                p[0] = ("igualdad", p[2], p[1], p[3])


def p_rel(p):
    '''rel : expr op_rel expr
            | expr'''
    global if_code
    if len(p) == 2:
        p[0] = ("rel", p[1])  # El árbol de análisis sintáctico simplemente toma el rel directamente
    else:
        primero = recorrer_arbol_retornar_ultimo(p[1])
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        boleana = 'false'
        num1 = 0
        num2 = 0
        if_code = if_code + ' ' + str(primero) + ' ' + p[2][1] + ' ' + str(segundo) + 'ç'
        if isinstance(primero, str):
            if primero in table:
                (tipe, nombre, value) = table[primero]
                num1 = value
            else:
                entry3.insert(1.0, f'Error variable {primero} no declarada \n')
                p[0] = ("rel", p[2], p[1], p[3])
        elif isinstance(primero, int) or isinstance(primero, float):
            num1 = primero
        if isinstance(segundo, str):
            if segundo in table:
                (tipe, nombre, value) = table[segundo]
                num2 = value
            else:
                entry3.insert(1.0, f'Error variable {segundo} no declarada \n')
                p[0] = ("rel", p[2], p[1], p[3])
        elif isinstance(segundo, int) or isinstance(segundo, float):
            num2 = segundo
        if p[2][1] == '<=':
            if num1 <= num2: boleana = 'true'
        elif p[2][1] == '>=':
            if num1 >= num2: boleana = 'true'
        elif p[2][1] == '>':
            if num1 > num2: boleana = 'true'
        elif p[2][1] == '<':
            if num1 < num2: boleana = 'true'
        p[0] = ("rel", boleana)
    return if_code


def p_op_rel(p):
    '''op_rel : LEESTHAN
              | MORETHAN
              | LEESETHAN
              | MOREETHAN'''
    p[0] = ('op_rel', p[1])  # El árbol de análisis sintáctico simplemente toma el operador de comparación directamente


def p_expr(p):
    '''expr : expr MINUS term
            | expr PLUS term
            | term'''
    global code
    if len(p) == 2:
        p[0] = ('expr', p[1])  # El árbol de análisis sintáctico simplemente toma el term directamente
    else:
        primero = recorrer_arbol_retornar_ultimo(p[1])
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        # saber si es una constante o un factor
        valor = 0
        if isinstance(primero, str):
            if primero in table:
                (variable_type, variable_name, variable_valor) = table[primero]
                primero = variable_valor
                valor = valor + 1
            else:
                entry3.insert(1.0, f'Error variable {primero}no declarada  \n')
                p[0] = ('expr', p[2], p[1], p[3])
        if isinstance(segundo, str):
            if segundo in table:
                (variable_type, variable_name, variable_valor) = table[segundo]
                segundo = variable_valor
                valor = valor + 1
            else:
                entry3.insert(1.0, f'Error variable {segundo} no declarada  \n')
                p[0] = ('expr', p[2], p[1], p[3])
        if valor == 2 or (valor == 1 and (isinstance(primero, int) or isinstance(primero, float))) or (
                valor == 1 and (isinstance(segundo, int) or isinstance(segundo, float))) or (
                (isinstance(primero, int) and isinstance(segundo, float)) or (
                isinstance(primero, int) and isinstance(segundo, int)) or (
                        isinstance(primero, float) and isinstance(segundo, float)) or (
                        isinstance(primero, float) and isinstance(segundo, int))):
            # revisar errores de tipo
            if isinstance(primero, int) and isinstance(segundo, int):
                if p[2] == "+":
                    p[0] = ('expr', int(primero + segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp + temp2' + '\n'
                else:
                    p[0] = ('expr', int(primero - segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp - temp2' + '\n'
            elif isinstance(primero, float) and isinstance(segundo, float):
                if p[2] == "+":
                    p[0] = ('expr', float(primero + segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp + temp2' + '\n'
                else:
                    p[0] = ('expr', float(primero - segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp - temp2' + '\n'
            else:
                if p[2] == "+":
                    p[0] = ('expr', float(primero + segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp + temp2' + '\n'
                else:
                    p[0] = ('expr', float(primero - segundo))
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp - temp2' + '\n'
        # p[0] = ('expr',p[2], p[1], p[3])  # El árbol de análisis sintáctico tiene el operador y los términos correspondientes
        # p[0] = ('expr', suma aqui)
        return code


def p_term(p):
    '''term : term TIMES unario
            | term DIVIDE unario
            | unario'''
    global code
    if len(p) == 2:
        p[0] = ('term', p[1])  # El árbol de análisis sintáctico simplemente toma el unario directamente
    else:
        primero = recorrer_arbol_retornar_ultimo(p[1])
        segundo = recorrer_arbol_retornar_ultimo(p[3])
        # saber si es una constante o un factor
        valor = 0
        if isinstance(primero, str):
            if primero in table:
                (variable_type, variable_name, variable_valor) = table[primero]
                primero = variable_valor
                valor = valor + 1
            else:
                entry3.insert(1.0, f'Error variable {primero}no declarada  \n')
                p[0] = ('expr', p[2], p[1], p[3])
        if isinstance(segundo, str):
            if segundo in table:
                (variable_type, variable_name, variable_valor) = table[segundo]
                segundo = variable_valor
                valor = valor + 1
            else:
                entry3.insert(1.0, f'Error variable {segundo} no declarada  \n')
                p[0] = ('expr', p[2], p[1], p[3])
        if valor == 2 or (valor == 1 and (isinstance(primero, int) or isinstance(primero, float))) or (
                valor == 1 and (isinstance(segundo, int) or isinstance(segundo, float))) or (
                (isinstance(primero, int) and isinstance(segundo, float)) or (
                isinstance(primero, int) and isinstance(segundo, int)) or (
                        isinstance(primero, float) and isinstance(segundo, float)) or (
                        isinstance(primero, float) and isinstance(segundo, int))):
            if p[2] == '*':
                p[0] = ('expr', (primero * segundo))
                code = code + ' temp = ' + str(primero) + '\n'
                code = code + ' temp2 = ' + str(segundo) + '\n'
                code = code + ' temp3 = ' + ' temp * temp2' + '\n'
            elif p[2] == '/':
                if int(segundo) == 0:
                    entry3.insert(1.0, f'Error en division al dividir entre 0  \n')
                    p[0] = ('expr', 0)
                else:
                    resultado = primero / segundo if primero % segundo != 0 else primero // segundo
                    p[0] = ('expr', resultado)
                    code = code + ' temp = ' + str(primero) + '\n'
                    code = code + ' temp2 = ' + str(segundo) + '\n'
                    code = code + ' temp3 = ' + ' temp / temp2' + '\n'
            else:
                p[0] = ('term', p[2], p[1],
                        p[3])  # El árbol de análisis sintáctico tiene el operador y los términos correspondientes
    return code


def p_unario(p):
    '''unario : NOT unario
              | MINUS unario
              | factor'''
    if len(p) == 2:
        p[0] = ('unario', p[1])
    else:
        p[0] = ('unario', p[1], p[2])


def p_factor(p):
    '''factor : LPAREN RPAREN
              | ID
              | NUMBER
              | DOUBLE
              | TRUE
              | FALSE'''
    if len(p) == 2:
        p[0] = ('factor', p[1])
    else:
        p[0] = ('factor', p[2])


def recorrer_arbol_retornar_ultimo(arbol):
    if isinstance(arbol, tuple):
        nodo = arbol[0]
        for subarbol in arbol[1:]:
            ultimo_nodo = recorrer_arbol_retornar_ultimo(subarbol)
        return ultimo_nodo
    else:
        return arbol


def obtener_datos_traza(traza):
    if traza[0] == 'exp_bool':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'comb':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'igualdad':
        izquierda = obtener_datos_traza(traza[1])
        operador = traza[1][0][1]
        derecha = obtener_datos_traza(traza[1][2])
        return izquierda, operador, derecha
    elif traza[0] == 'rel':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'op_rel':
        return traza[1]
    elif traza[0] == 'expr':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'term':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'unario':
        return obtener_datos_traza(traza[1])
    elif traza[0] == 'factor':
        return traza[1]
    else:
        raise ValueError(f"Elemento no reconocido en la traza: {traza}")


def cambiaPalabra():
    global asm_code, labels, labelsE, relacionales, if_code, primera
    primera = 0
    asm_code = ''
    if_code = ""
    relacionales = []
    labels = 1
    labelsE = 1
    table.clear()
    errorBox.delete("1.0", "end")
    os.chdir("C:/Users/Artur/Desktop/COMPILADORES ll/proyecto v2.0/")
    print(os.getcwd())
    archivo_salida = open("erroresLexer.txt", "w")
    archivo_salida.write("")
    entry1.delete(1.0, END)
    entry2.delete(1.0, END)
    entry3.delete(1.0, END)
    entry4.delete(1.0, END)
    entry5.delete(1.0, END)
    lexString = ""
    result = ""
    parser = ""
    dataForYacc = ""
    image = ""
    photo = ""
    tokens_formateados = []
    dataForLexer = textBox.get(1.0, END)
    dataForYacc = textBox.get(1.0, END)
    print(dataForLexer)
    lexer = lex.lex()
    lexer.input(dataForLexer)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
        lexString += str(tok) + "\n"
        token_formateado = f"{tok.type}\t\t{tok.value}\t\t{tok.lineno}\t\t{tok.lexpos}\n"
        tokens_formateados.append(token_formateado)

    dataForLexer = "Clave\t\tLexema\t\tFila\t\tColumna\n" + "".join(tokens_formateados)
    # ANALIZADOR SINTACTICO
    try:
        parser = yacc.yacc()
        result = parser.parse(dataForYacc)
        print(result)
        print_tree(result)
        simbolos_forms = []
        for variable_name, variable_info in table.items():
            iden, name, value = variable_info
            simbolos_form = f"{iden}\t\t{name}\t\t{value}\n"
            simbolos_forms.append(simbolos_form)
            print(simbolos_form)
        dataForYac = "Tipo\t\tNombre\t\tValor\n" + "".join(simbolos_forms)
        dot.format = 'png'  # Puedes cambiar el formato a 'pdf', 'svg', etc.
        dot.render('C:/Users/Artur/Desktop/COMPILADORES ll/proyecto v2.0/syntax_tree')
    except Exception as exception:
        print('error', exception)
    entry1.insert(1.0, dataForLexer)
    entry2.insert(1.0, result)
    # entry4.insert(1.0, dataForYac)
    entry5.insert(1.0, asm_code)
    archivo_salida = open("salidaLexer.txt", "w")
    archivo_salida2 = open("salidaYacc.txt", "w")
    # Escribir contenido en el archivo
    archivo_salida.write(dataForLexer)
    archivo_salida2.write(str(result))
    # Cerrar el archivo
    archivo_salida.close()
    archivo_salida2.close()


def abrirArchivo():
    # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    print(filename)
    f = open(filename, "r")
    # Leer el contenido del archivo y guardarlo en una variable
    contenido = f.read()
    # Imprimir el contenido del archivo
    print(contenido)
    textBox.insert(1.0, contenido)
    # Cerrar el archivo
    f.close()


def guardarArchivo():
    f = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
    if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
        return
    text2save = str(textBox.get(1.0, END))  # starts from `1.0`, not `0.0`
    f.write(text2save)
    f.close()  # `()` was missing.


dot = graphviz.Digraph()
app = tk.Tk()
app.geometry("1200x600")  # Anchura por altura
app.configure(background="#005555")
app.title("Compilador")
app.columnconfigure(index=0, weight=3)
app.rowconfigure(index=1, weight=3)

# Interfaz
barra_menu = tk.Frame(app, bg="#003535", height=40)
barra_menu.grid(row=0, column=0, columnspan=3, sticky="ew")

boton1 = tk.Button(barra_menu, text="Run", command=cambiaPalabra, bg="#002525", width=5, height=2)
boton2 = tk.Button(barra_menu, text="Abrir Archivo", command=abrirArchivo, bg="#002525", height=2)
boton3 = tk.Button(barra_menu, text="Guardar Archivo", command=guardarArchivo, bg="#002525", height=2)

boton1.grid(row=0, column=0, padx=5)
boton2.grid(row=0, column=1, padx=5)
boton3.grid(row=0, column=2, padx=5)

textBox = tk.Text(app)
textBox.grid(row=1, column=0, columnspan=2, sticky="N", padx=(30, 5), pady=(30, 0))

notebook = ttk.Notebook(app)

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
tab3 = ttk.Frame(notebook)
tab4 = ttk.Frame(notebook)
tab5 = ttk.Frame(notebook)

notebook.add(tab1, text="Analisis Lexico")
notebook.add(tab2, text="Analisis Sintactico")
notebook.add(tab3, text="Analisis Semantico")
notebook.add(tab4, text="Tabla de Simbolos")
notebook.add(tab5, text="Generacion de codigo")

entry1 = tk.Text(tab1)
entry2 = tk.Text(tab2)
entry3 = tk.Text(tab3)
entry4 = tk.Text(tab4)
entry5 = tk.Text(tab5)

entry1.pack()
entry2.pack()
entry3.pack()
entry4.pack()
entry5.pack()

notebook.grid(row=1, column=2, rowspan=2, sticky="NW", padx=(5, 30), pady=(70, 0))

errorBox = tk.Text(app, height=10)
errorBox.grid(row=2, column=0, columnspan=2, sticky="EW", padx=(30, 5), pady=(0, 50))

app.mainloop()