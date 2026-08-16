#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Simples: Algoritmos de Higgins vs Cai & Goh
Análise de resultados de execução de testes de otimização ferroviária
"""

import os
import re
from pathlib import Path

class AnalisadorSimples:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.resultados = {
            'higgins': [],  # CPLEX
            'cai_goh': []   # Java
        }
        
    def extrair_dados_cplex(self, arquivo):
        """Extrai dados de execução dos arquivos CPLEX (Higgins)"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Extrair tempo de execução
            tempo_match = re.search(r'Tempo de execução do modelo: ([\d.]+) segundos', conteudo)
            tempo_execucao = float(tempo_match.group(1)) if tempo_match else None
            
            # Extrair status da solução
            status_match = re.search(r'Status da solução: (\w+)', conteudo)
            status = status_match.group(1) if status_match else 'UNKNOWN'
            
            # Extrair informações do nome do arquivo
            nome_arquivo = Path(arquivo).name
            match = re.search(r'(\w+)-cruza-5e-(\d+)d-(\d+)c-(\d+)t', nome_arquivo)
            if match:
                distribuicao = match.group(1)
                dias = int(match.group(2))
                carros = int(match.group(3))
                trens = int(match.group(4))
            else:
                distribuicao = 'unknown'
                dias = carros = trens = 0
                
            return {
                'algoritmo': 'Higgins (CPLEX)',
                'arquivo': nome_arquivo,
                'distribuicao': distribuicao,
                'dias': dias,
                'carros': carros,
                'trens': trens,
                'tempo_execucao': tempo_execucao,
                'status': status,
                'complexidade': f"{carros}c-{trens}t"
            }
        except Exception as e:
            print(f"Erro ao processar arquivo CPLEX {arquivo}: {e}")
            return None
    
    def extrair_dados_java(self, arquivo):
        """Extrai dados de execução dos arquivos Java (Cai & Goh)"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Extrair tempo de execução
            tempo_match = re.search(r'Tempo de execução do algoritmo: (\d+)', conteudo)
            tempo_execucao = int(tempo_match.group(1)) if tempo_match else 0
            
            # Extrair informações do nome do arquivo
            nome_arquivo = Path(arquivo).name
            match = re.search(r'(\w+)-cruza-5e-(\d+)d-(\d+)c-(\d+)t', nome_arquivo)
            if match:
                distribuicao = match.group(1)
                dias = int(match.group(2))
                carros = int(match.group(3))
                trens = int(match.group(4))
            else:
                distribuicao = 'unknown'
                dias = carros = trens = 0
                
            # Calcular makespan aproximado baseado nos horários dos trens
            makespan = self.calcular_makespan_java(conteudo)
                
            return {
                'algoritmo': 'Cai & Goh (Java)',
                'arquivo': nome_arquivo,
                'distribuicao': distribuicao,
                'dias': dias,
                'carros': carros,
                'trens': trens,
                'tempo_execucao': tempo_execucao,
                'status': 'COMPLETED',
                'complexidade': f"{carros}c-{trens}t",
                'makespan': makespan
            }
        except Exception as e:
            print(f"Erro ao processar arquivo Java {arquivo}: {e}")
            return None
    
    def calcular_makespan_java(self, conteudo):
        """Calcula o makespan aproximado baseado nos horários dos trens"""
        try:
            # Extrair horários de chegada dos trens
            horarios = re.findall(r'\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}:\d{2})', conteudo)
            if horarios:
                # Converter para minutos desde meia-noite
                minutos = []
                for horario in horarios:
                    h, m, s = map(int, horario.split(':'))
                    minutos.append(h * 60 + m)
                
                if minutos:
                    return max(minutos) - min(minutos)
            return None
        except:
            return None
    
    def coletar_dados(self):
        """Coleta todos os dados de execução do workspace"""
        print("Coletando dados de execução...")
        
        # Procurar arquivos CPLEX (Higgins)
        for arquivo in self.workspace_path.rglob("*cplex.txt"):
            if "dados_execucao" in arquivo.name:
                dados = self.extrair_dados_cplex(arquivo)
                if dados:
                    self.resultados['higgins'].append(dados)
        
        # Procurar arquivos Java (Cai & Goh)
        for arquivo in self.workspace_path.rglob("saida_dados_java.txt"):
            dados = self.extrair_dados_java(arquivo)
            if dados:
                self.resultados['cai_goh'].append(dados)
        
        print(f"Dados coletados: {len(self.resultados['higgins'])} CPLEX, {len(self.resultados['cai_goh'])} Java")
    
    def calcular_estatisticas(self, dados_list):
        """Calcula estatísticas básicas para uma lista de dados"""
        if not dados_list:
            return None
            
        tempos = [d['tempo_execucao'] for d in dados_list if d['tempo_execucao'] is not None]
        trens = [d['trens'] for d in dados_list]
        
        if not tempos:
            return None
            
        return {
            'count': len(dados_list),
            'tempo_medio': sum(tempos) / len(tempos),
            'tempo_min': min(tempos),
            'tempo_max': max(tempos),
            'trens_medio': sum(trens) / len(trens),
            'trens_max': max(trens)
        }
    
    def gerar_relatorio(self):
        """Gera relatório textual detalhado"""
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO COMPARATIVO: ALGORITMOS DE HIGGINS vs CAI & GOH")
        relatorio.append("=" * 80)
        relatorio.append("")
        
        # Resumo executivo
        relatorio.append("RESUMO EXECUTIVO")
        relatorio.append("-" * 40)
        total_higgins = len(self.resultados['higgins'])
        total_cai_goh = len(self.resultados['cai_goh'])
        relatorio.append(f"Total de testes analisados: {total_higgins + total_cai_goh}")
        relatorio.append(f"Testes CPLEX (Higgins): {total_higgins}")
        relatorio.append(f"Testes Java (Cai & Goh): {total_cai_goh}")
        relatorio.append("")
        
        # Análise de tempo de execução
        relatorio.append("ANÁLISE DE TEMPO DE EXECUÇÃO")
        relatorio.append("-" * 40)
        
        # Estatísticas Higgins
        stats_higgins = self.calcular_estatisticas(self.resultados['higgins'])
        if stats_higgins:
            relatorio.append("Higgins (CPLEX):")
            relatorio.append(f"  - Tempo médio: {stats_higgins['tempo_medio']:.3f} segundos")
            relatorio.append(f"  - Tempo mínimo: {stats_higgins['tempo_min']:.3f} segundos")
            relatorio.append(f"  - Tempo máximo: {stats_higgins['tempo_max']:.3f} segundos")
            relatorio.append(f"  - Número médio de trens: {stats_higgins['trens_medio']:.1f}")
            relatorio.append("")
        
        # Estatísticas Cai & Goh
        stats_cai_goh = self.calcular_estatisticas(self.resultados['cai_goh'])
        if stats_cai_goh:
            relatorio.append("Cai & Goh (Java):")
            relatorio.append(f"  - Tempo médio: {stats_cai_goh['tempo_medio']:.3f} segundos")
            relatorio.append(f"  - Tempo mínimo: {stats_cai_goh['tempo_min']:.3f} segundos")
            relatorio.append(f"  - Tempo máximo: {stats_cai_goh['tempo_max']:.3f} segundos")
            relatorio.append(f"  - Número médio de trens: {stats_cai_goh['trens_medio']:.1f}")
            relatorio.append("")
        
        # Análise por complexidade
        relatorio.append("ANÁLISE POR COMPLEXIDADE")
        relatorio.append("-" * 40)
        
        # Agrupar por complexidade
        complexidades_higgins = {}
        complexidades_cai_goh = {}
        
        for dados in self.resultados['higgins']:
            comp = dados['complexidade']
            if comp not in complexidades_higgins:
                complexidades_higgins[comp] = []
            complexidades_higgins[comp].append(dados['tempo_execucao'])
        
        for dados in self.resultados['cai_goh']:
            comp = dados['complexidade']
            if comp not in complexidades_cai_goh:
                complexidades_cai_goh[comp] = []
            complexidades_cai_goh[comp].append(dados['tempo_execucao'])
        
        relatorio.append("Higgins (CPLEX) por complexidade:")
        for comp in sorted(complexidades_higgins.keys()):
            tempos = complexidades_higgins[comp]
            tempo_medio = sum(tempos) / len(tempos)
            relatorio.append(f"  - {comp}: {tempo_medio:.3f}s (n={len(tempos)})")
        
        relatorio.append("")
        relatorio.append("Cai & Goh (Java) por complexidade:")
        for comp in sorted(complexidades_cai_goh.keys()):
            tempos = complexidades_cai_goh[comp]
            tempo_medio = sum(tempos) / len(tempos)
            relatorio.append(f"  - {comp}: {tempo_medio:.3f}s (n={len(tempos)})")
        
        relatorio.append("")
        
        # Conclusões
        relatorio.append("CONCLUSÕES")
        relatorio.append("-" * 40)
        
        if stats_higgins and stats_cai_goh:
            # Determinar qual algoritmo é mais rápido
            if stats_higgins['tempo_medio'] < stats_cai_goh['tempo_medio']:
                razao = stats_cai_goh['tempo_medio'] / stats_higgins['tempo_medio']
                relatorio.append(f"• O algoritmo de Higgins (CPLEX) é em média {razao:.1f}x mais rápido")
            else:
                razao = stats_higgins['tempo_medio'] / stats_cai_goh['tempo_medio']
                relatorio.append(f"• O algoritmo de Cai & Goh (Java) é em média {razao:.1f}x mais rápido")
        
        # Análise de consistência
        if stats_higgins and stats_cai_goh:
            variacao_higgins = (stats_higgins['tempo_max'] - stats_higgins['tempo_min']) / stats_higgins['tempo_medio']
            variacao_cai_goh = (stats_cai_goh['tempo_max'] - stats_cai_goh['tempo_min']) / stats_cai_goh['tempo_medio']
            
            if variacao_higgins < variacao_cai_goh:
                relatorio.append("• O algoritmo de Higgins apresenta maior consistência no tempo de execução")
            else:
                relatorio.append("• O algoritmo de Cai & Goh apresenta maior consistência no tempo de execução")
        
        # Recomendações
        relatorio.append("")
        relatorio.append("RECOMENDAÇÕES")
        relatorio.append("-" * 40)
        relatorio.append("• Para problemas pequenos (1-3 trens): Ambos os algoritmos são adequados")
        relatorio.append("• Para problemas médios (4-6 trens): Considerar trade-off entre velocidade e qualidade")
        relatorio.append("• Para problemas grandes (7-8 trens): Avaliar requisitos específicos de tempo vs qualidade")
        relatorio.append("")
        
        return "\n".join(relatorio)
    
    def executar_analise(self):
        """Executa análise completa dos resultados"""
        print("Iniciando análise comparativa dos algoritmos...")
        
        # Coletar dados
        self.coletar_dados()
        
        # Gerar relatório
        relatorio = self.gerar_relatorio()
        
        # Salvar relatório
        with open('relatorio_analise_algoritmos.txt', 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        print("\nRelatório salvo em 'relatorio_analise_algoritmos.txt'")
        
        return relatorio

def main():
    """Função principal"""
    # Caminho do workspace
    workspace_path = "."
    
    # Criar analisador
    analisador = AnalisadorSimples(workspace_path)
    
    # Executar análise completa
    relatorio = analisador.executar_analise()
    
    # Exibir resumo
    print("\n" + "="*80)
    print("RESUMO DA ANÁLISE")
    print("="*80)
    print(relatorio)

if __name__ == "__main__":
    main() 