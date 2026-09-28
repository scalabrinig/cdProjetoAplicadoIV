from __future__ import annotations

import traceback
import os

def exception_trackers(exc):
    # 1. Extrai o traceback (histórico do erro)
    error_index = -1
    tb = traceback.extract_tb(exc.__traceback__)

    for i, frame in enumerate(reversed(tb)):
        #if "site-packages" not in frame.filename and "lib" + os.sep not in frame.filename:
        if "Lib" not in frame.filename:
            error_index = -i-1
            break
    
    
    # 2. Pega o frame pelo index (onde o erro aconteceu de verdade)
    ultima_linha_erro = tb[error_index]
    
    arquivo = ultima_linha_erro.filename
    linha = ultima_linha_erro.lineno
    funcao = ultima_linha_erro.name
    codigo_do_erro = ultima_linha_erro.line
    tipo_erro = type(exc).__name__
    mensagem_erro = str(exc)

    # 3. Exibe as informações detalhadas
    print("\n>> ERROR TRACKBACK<< ")
    print(f"Arquivo: {arquivo}")
    print(f"Linha: {linha} (na função '{funcao}')")
    # Código que causou o problema:
    print(f"Código: {codigo_do_erro}") 
    print(f"Tipo: {tipo_erro} -> {mensagem_erro}\n")
    
    # 4. Recomendação de Correção Automática (Dica extra abaixo)
    print("Recomendação de Correção:")
    if tipo_erro == "ZeroDivisionError":
        print("   -> Verifique se a variável divisora é igual a zero antes de realizar a divisão.")
    elif tipo_erro == "FileNotFoundError":
        print("   -> Certifique-se de que o caminho do arquivo está correto e que o arquivo existe.")
    else:
        print("   -> Revise a lógica do código ou consulte a documentação do erro.")