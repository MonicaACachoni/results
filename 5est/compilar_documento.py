#!/usr/bin/env python3
"""
Script para compilar o documento LaTeX de comparativo CPLEX vs Java
"""

import subprocess
import os
import sys

def compilar_latex(arquivo_tex):
    """
    Compila um arquivo LaTeX em PDF
    """
    try:
        # Primeira compilação
        print("Compilando LaTeX (primeira passagem)...")
        resultado = subprocess.run([
            'pdflatex', 
            '-interaction=nonstopmode', 
            arquivo_tex
        ], capture_output=True, text=True)
        
        if resultado.returncode != 0:
            print("Erro na primeira compilação:")
            print(resultado.stderr)
            return False
        
        # Segunda compilação para resolver referências
        print("Compilando LaTeX (segunda passagem)...")
        resultado = subprocess.run([
            'pdflatex', 
            '-interaction=nonstopmode', 
            arquivo_tex
        ], capture_output=True, text=True)
        
        if resultado.returncode != 0:
            print("Erro na segunda compilação:")
            print(resultado.stderr)
            return False
        
        print(f"Documento compilado com sucesso: {arquivo_tex.replace('.tex', '.pdf')}")
        return True
        
    except FileNotFoundError:
        print("Erro: pdflatex não encontrado. Certifique-se de que o LaTeX está instalado.")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

def main():
    """
    Função principal
    """
    arquivo_tex = "comparativo_cplex_java.tex"
    
    if not os.path.exists(arquivo_tex):
        print(f"Erro: Arquivo {arquivo_tex} não encontrado.")
        return
    
    print("Iniciando compilação do documento LaTeX...")
    print(f"Arquivo: {arquivo_tex}")
    print("-" * 50)
    
    if compilar_latex(arquivo_tex):
        print("\nCompilação concluída com sucesso!")
        print("Arquivo PDF gerado: comparativo_cplex_java.pdf")
    else:
        print("\nFalha na compilação.")
        sys.exit(1)

if __name__ == "__main__":
    main() 