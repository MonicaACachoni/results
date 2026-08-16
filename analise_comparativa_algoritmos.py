#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Comparativa: Algoritmos de Higgins vs Cai & Goh
Análise de resultados de execução de testes de otimização ferroviária
"""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

class AnalisadorResultados:
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
    
    def criar_dataframe(self):
        """Cria DataFrame com todos os resultados"""
        todos_dados = []
        
        for algoritmo, dados_list in self.resultados.items():
            for dados in dados_list:
                todos_dados.append(dados)
        
        return pd.DataFrame(todos_dados)
    
    def analisar_desempenho(self, df):
        """Análise de desempenho dos algoritmos"""
        print("\n=== ANÁLISE DE DESEMPENHO ===")
        
        # Estatísticas por algoritmo
        stats = df.groupby('algoritmo').agg({
            'tempo_execucao': ['mean', 'std', 'min', 'max'],
            'trens': ['mean', 'max']
        }).round(3)
        
        print("\nEstatísticas de Tempo de Execução:")
        print(stats)
        
        # Análise por complexidade
        print("\n=== ANÁLISE POR COMPLEXIDADE ===")
        complexidade_stats = df.groupby(['algoritmo', 'complexidade']).agg({
            'tempo_execucao': 'mean',
            'trens': 'first'
        }).round(3)
        
        print(complexidade_stats)
        
        return stats, complexidade_stats
    
    def gerar_graficos(self, df):
        """Gera gráficos comparativos"""
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Comparação: Algoritmo de Higgins vs Cai & Goh', fontsize=16)
        
        # Gráfico 1: Tempo de execução por algoritmo
        ax1 = axes[0, 0]
        sns.boxplot(data=df, x='algoritmo', y='tempo_execucao', ax=ax1)
        ax1.set_title('Tempo de Execução por Algoritmo')
        ax1.set_ylabel('Tempo (segundos)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico 2: Tempo vs Número de Trens
        ax2 = axes[0, 1]
        for algoritmo in df['algoritmo'].unique():
            dados_algo = df[df['algoritmo'] == algoritmo]
            ax2.scatter(dados_algo['trens'], dados_algo['tempo_execucao'], 
                       label=algoritmo, alpha=0.7)
        ax2.set_title('Tempo de Execução vs Número de Trens')
        ax2.set_xlabel('Número de Trens')
        ax2.set_ylabel('Tempo (segundos)')
        ax2.legend()
        
        # Gráfico 3: Distribuição de complexidades
        ax3 = axes[1, 0]
        complexidade_counts = df.groupby(['algoritmo', 'complexidade']).size().unstack(fill_value=0)
        complexidade_counts.plot(kind='bar', ax=ax3)
        ax3.set_title('Distribuição de Complexidades por Algoritmo')
        ax3.set_ylabel('Número de Testes')
        ax3.tick_params(axis='x', rotation=45)
        
        # Gráfico 4: Makespan (se disponível)
        ax4 = axes[1, 1]
        df_makespan = df[df['makespan'].notna()]
        if not df_makespan.empty:
            sns.boxplot(data=df_makespan, x='algoritmo', y='makespan', ax=ax4)
            ax4.set_title('Makespan por Algoritmo')
            ax4.set_ylabel('Makespan (minutos)')
        else:
            ax4.text(0.5, 0.5, 'Dados de Makespan\nnão disponíveis', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Makespan por Algoritmo')
        
        plt.tight_layout()
        plt.savefig('comparacao_algoritmos.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def gerar_relatorio(self, df, stats, complexidade_stats):
        """Gera relatório textual detalhado"""
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO COMPARATIVO: ALGORITMOS DE HIGGINS vs CAI & GOH")
        relatorio.append("=" * 80)
        relatorio.append("")
        
        # Resumo executivo
        relatorio.append("RESUMO EXECUTIVO")
        relatorio.append("-" * 40)
        relatorio.append(f"Total de testes analisados: {len(df)}")
        relatorio.append(f"Testes CPLEX (Higgins): {len(df[df['algoritmo'] == 'Higgins (CPLEX)'])}")
        relatorio.append(f"Testes Java (Cai & Goh): {len(df[df['algoritmo'] == 'Cai & Goh (Java)'])}")
        relatorio.append("")
        
        # Análise de tempo de execução
        relatorio.append("ANÁLISE DE TEMPO DE EXECUÇÃO")
        relatorio.append("-" * 40)
        
        for algoritmo in df['algoritmo'].unique():
            dados_algo = df[df['algoritmo'] == algoritmo]
            tempo_medio = dados_algo['tempo_execucao'].mean()
            tempo_std = dados_algo['tempo_execucao'].std()
            tempo_min = dados_algo['tempo_execucao'].min()
            tempo_max = dados_algo['tempo_execucao'].max()
            
            relatorio.append(f"{algoritmo}:")
            relatorio.append(f"  - Tempo médio: {tempo_medio:.3f} ± {tempo_std:.3f} segundos")
            relatorio.append(f"  - Tempo mínimo: {tempo_min:.3f} segundos")
            relatorio.append(f"  - Tempo máximo: {tempo_max:.3f} segundos")
            relatorio.append("")
        
        # Análise de escalabilidade
        relatorio.append("ANÁLISE DE ESCALABILIDADE")
        relatorio.append("-" * 40)
        
        for algoritmo in df['algoritmo'].unique():
            dados_algo = df[df['algoritmo'] == algoritmo]
            correlacao = dados_algo['trens'].corr(dados_algo['tempo_execucao'])
            relatorio.append(f"{algoritmo}:")
            relatorio.append(f"  - Correlação trens vs tempo: {correlacao:.3f}")
            
            # Análise por faixa de complexidade
            faixas = [(1, 3), (4, 6), (7, 8)]
            for min_trens, max_trens in faixas:
                faixa_dados = dados_algo[(dados_algo['trens'] >= min_trens) & 
                                       (dados_algo['trens'] <= max_trens)]
                if not faixa_dados.empty:
                    tempo_medio_faixa = faixa_dados['tempo_execucao'].mean()
                    relatorio.append(f"  - {min_trens}-{max_trens} trens: {tempo_medio_faixa:.3f}s")
            relatorio.append("")
        
        # Conclusões
        relatorio.append("CONCLUSÕES")
        relatorio.append("-" * 40)
        
        # Determinar qual algoritmo é mais rápido
        tempo_higgins = df[df['algoritmo'] == 'Higgins (CPLEX)']['tempo_execucao'].mean()
        tempo_cai_goh = df[df['algoritmo'] == 'Cai & Goh (Java)']['tempo_execucao'].mean()
        
        if tempo_higgins < tempo_cai_goh:
            relatorio.append(f"• O algoritmo de Higgins (CPLEX) é em média {tempo_cai_goh/tempo_higgins:.1f}x mais rápido")
        else:
            relatorio.append(f"• O algoritmo de Cai & Goh (Java) é em média {tempo_higgins/tempo_cai_goh:.1f}x mais rápido")
        
        # Análise de consistência
        std_higgins = df[df['algoritmo'] == 'Higgins (CPLEX)']['tempo_execucao'].std()
        std_cai_goh = df[df['algoritmo'] == 'Cai & Goh (Java)']['tempo_execucao'].std()
        
        if std_higgins < std_cai_goh:
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
    
    def executar_analise_completa(self):
        """Executa análise completa dos resultados"""
        print("Iniciando análise comparativa dos algoritmos...")
        
        # Coletar dados
        self.coletar_dados()
        
        # Criar DataFrame
        df = self.criar_dataframe()
        
        if df.empty:
            print("Nenhum dado encontrado para análise!")
            return
        
        # Análise de desempenho
        stats, complexidade_stats = self.analisar_desempenho(df)
        
        # Gerar gráficos
        self.gerar_graficos(df)
        
        # Gerar relatório
        relatorio = self.gerar_relatorio(df, stats, complexidade_stats)
        
        # Salvar relatório
        with open('relatorio_analise_algoritmos.txt', 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        print("\nRelatório salvo em 'relatorio_analise_algoritmos.txt'")
        print("Gráficos salvos em 'comparacao_algoritmos.png'")
        
        return df, stats, relatorio

def main():
    """Função principal"""
    # Caminho do workspace
    workspace_path = "/c%3A/Users/monic/Dropbox/CenariosTestes/resultados"
    
    # Criar analisador
    analisador = AnalisadorResultados(workspace_path)
    
    # Executar análise completa
    df, stats, relatorio = analisador.executar_analise_completa()
    
    # Exibir resumo
    print("\n" + "="*80)
    print("RESUMO DA ANÁLISE")
    print("="*80)
    print(relatorio)

if __name__ == "__main__":
    main() 