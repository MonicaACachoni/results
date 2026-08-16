#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Completa de Resultados de Testes Ferroviários
Organização por Estações, Quilometragens e Minutos
"""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class AnalisadorCompletoResultados:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.resultados_por_estacoes = {}
        self.resultados_por_km = {}
        self.resultados_por_minutos = {}
        self.dados_consolidados = []
        
    def extrair_parametros_cenario(self, nome_arquivo):
        """Extrai parâmetros do cenário do nome do arquivo"""
        # Padrão: distribuicao-cruza-5e-XXd-XXc-XXt-XXv-XXs-XXi-XXp-XXr-XXm-XXh-XXb-XXk
        match = re.search(r'(\w+)-cruza-5e-(\d+)d-(\d+)c-(\d+)t-(\d+)v-(\d+)s-(\d+)i-(\d+)p-(\d+)r-(\d+)m-(\d+)h-(\d+)b-(\d+)k', nome_arquivo)
        if match:
            return {
                'distribuicao': match.group(1),
                'dias': int(match.group(2)),
                'carros': int(match.group(3)),
                'trens': int(match.group(4)),
                'velocidade': int(match.group(5)),
                'seguimentos': int(match.group(6)),
                'intervalo': int(match.group(7)),
                'passageiros': int(match.group(8)),
                'recursos': int(match.group(9)),
                'manutencao': int(match.group(10)),
                'horarios': int(match.group(11)),
                'bifurcacoes': int(match.group(12)),
                'quilometragem': int(match.group(13))
            }
        return None
    
    def extrair_dados_java(self, arquivo):
        """Extrai dados dos arquivos Java (Cai & Goh)"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            dados_cenarios = []
            cenarios = conteudo.split('Cenário=>')
            
            for cenario in cenarios[1:]:  # Pular o primeiro elemento vazio
                linhas = cenario.strip().split('\n')
                if not linhas:
                    continue
                    
                # Primeira linha contém o nome do cenário e tempo de execução
                primeira_linha = linhas[0]
                tempo_match = re.search(r'Tempo de execução do algoritmo: (\d+)', primeira_linha)
                tempo_execucao = int(tempo_match.group(1)) if tempo_match else 0
                
                # Extrair nome do cenário
                nome_cenario = primeira_linha.split('Tempo de execução')[0].strip()
                parametros = self.extrair_parametros_cenario(nome_cenario)
                
                if not parametros:
                    continue
                
                # Analisar horários dos trens
                horarios_chegada = []
                horarios_partida = []
                duracao_viagens = []
                
                for linha in linhas[1:]:
                    if linha.startswith('Trem') and '\t' in linha:
                        partes = linha.split('\t')
                        if len(partes) >= 4:
                            # Extrair horários de partida e chegada
                            partida = partes[1]
                            chegada = partes[2]
                            duracao = partes[3]
                            
                            # Converter para minutos desde meia-noite
                            try:
                                h_partida, m_partida, s_partida = map(int, partida.split('T')[1].split(':'))
                                h_chegada, m_chegada, s_chegada = map(int, chegada.split('T')[1].split(':'))
                                
                                minutos_partida = h_partida * 60 + m_partida
                                minutos_chegada = h_chegada * 60 + m_chegada
                                
                                horarios_partida.append(minutos_partida)
                                horarios_chegada.append(minutos_chegada)
                                duracao_viagens.append(minutos_chegada - minutos_partida)
                            except:
                                continue
                
                if horarios_chegada:
                    makespan = max(horarios_chegada) - min(horarios_partida)
                    tempo_medio_viagem = np.mean(duracao_viagens) if duracao_viagens else 0
                else:
                    makespan = 0
                    tempo_medio_viagem = 0
                
                dados_cenarios.append({
                    'algoritmo': 'Cai & Goh (Java)',
                    'cenario': nome_cenario,
                    'tempo_execucao': tempo_execucao,
                    'makespan': makespan,
                    'tempo_medio_viagem': tempo_medio_viagem,
                    'num_trens': len(horarios_chegada),
                    **parametros
                })
            
            return dados_cenarios
            
        except Exception as e:
            print(f"Erro ao processar arquivo Java {arquivo}: {e}")
            return []
    
    def extrair_dados_cplex(self, arquivo):
        """Extrai dados dos arquivos CPLEX (Higgins)"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Extrair tempo de execução
            tempo_match = re.search(r'Tempo de execução do modelo: ([\d.]+) segundos', conteudo)
            tempo_execucao = float(tempo_match.group(1)) if tempo_match else 0
            
            # Extrair status da solução
            status_match = re.search(r'Status da solução: (\w+)', conteudo)
            status = status_match.group(1) if status_match else 'UNKNOWN'
            
            # Extrair informações do nome do arquivo
            nome_arquivo = Path(arquivo).name
            parametros = self.extrair_parametros_cenario(nome_arquivo)
            
            if not parametros:
                return None
            
            return {
                'algoritmo': 'Higgins (CPLEX)',
                'cenario': nome_arquivo,
                'tempo_execucao': tempo_execucao,
                'status': status,
                'makespan': None,  # CPLEX não fornece makespan diretamente
                'tempo_medio_viagem': None,
                'num_trens': parametros['trens'],
                **parametros
            }
            
        except Exception as e:
            print(f"Erro ao processar arquivo CPLEX {arquivo}: {e}")
            return None
    
    def coletar_todos_dados(self):
        """Coleta todos os dados de execução organizados por categorias"""
        print("Coletando dados de execução...")
        
        # Procurar arquivos Java (Cai & Goh)
        for arquivo in self.workspace_path.rglob("saida_dados_java.txt"):
            dados = self.extrair_dados_java(arquivo)
            self.dados_consolidados.extend(dados)
        
        # Procurar arquivos CPLEX (Higgins)
        for arquivo in self.workspace_path.rglob("*cplex.txt"):
            if "dados_execucao" in arquivo.name:
                dados = self.extrair_dados_cplex(arquivo)
                if dados:
                    self.dados_consolidados.append(dados)
        
        print(f"Total de dados coletados: {len(self.dados_consolidados)}")
        
        # Organizar por categorias
        self.organizar_por_categorias()
    
    def organizar_por_categorias(self):
        """Organiza os dados por estações, quilometragens e minutos"""
        df = pd.DataFrame(self.dados_consolidados)
        
        if df.empty:
            print("Nenhum dado encontrado!")
            return
        
        # Organizar por estações (baseado no número de trens como proxy)
        self.resultados_por_estacoes = df.groupby('num_trens').agg({
            'tempo_execucao': ['mean', 'std', 'min', 'max', 'count'],
            'makespan': ['mean', 'std', 'min', 'max'],
            'tempo_medio_viagem': ['mean', 'std', 'min', 'max'],
            'algoritmo': lambda x: x.value_counts().to_dict()
        }).round(3)
        
        # Organizar por quilometragens
        if 'quilometragem' in df.columns:
            self.resultados_por_km = df.groupby('quilometragem').agg({
                'tempo_execucao': ['mean', 'std', 'min', 'max', 'count'],
                'makespan': ['mean', 'std', 'min', 'max'],
                'tempo_medio_viagem': ['mean', 'std', 'min', 'max'],
                'algoritmo': lambda x: x.value_counts().to_dict()
            }).round(3)
        
        # Organizar por minutos (intervalo de tempo)
        if 'intervalo' in df.columns:
            self.resultados_por_minutos = df.groupby('intervalo').agg({
                'tempo_execucao': ['mean', 'std', 'min', 'max', 'count'],
                'makespan': ['mean', 'std', 'min', 'max'],
                'tempo_medio_viagem': ['mean', 'std', 'min', 'max'],
                'algoritmo': lambda x: x.value_counts().to_dict()
            }).round(3)
    
    def gerar_graficos_por_categorias(self):
        """Gera gráficos organizados por categorias"""
        df = pd.DataFrame(self.dados_consolidados)
        
        if df.empty:
            print("Nenhum dado para gerar gráficos!")
            return
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        
        # Gráfico 1: Análise por Número de Trens (Estações)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Análise de Resultados por Categorias', fontsize=16)
        
        # Tempo de execução por número de trens
        ax1 = axes[0, 0]
        for algoritmo in df['algoritmo'].unique():
            dados_algo = df[df['algoritmo'] == algoritmo]
            tempo_por_trens = dados_algo.groupby('num_trens')['tempo_execucao'].mean()
            ax1.plot(tempo_por_trens.index, tempo_por_trens.values, 
                    marker='o', label=algoritmo, linewidth=2)
        ax1.set_title('Tempo de Execução vs Número de Trens')
        ax1.set_xlabel('Número de Trens')
        ax1.set_ylabel('Tempo de Execução (segundos)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Makespan por número de trens
        ax2 = axes[0, 1]
        df_makespan = df[df['makespan'].notna()]
        if not df_makespan.empty:
            for algoritmo in df_makespan['algoritmo'].unique():
                dados_algo = df_makespan[df_makespan['algoritmo'] == algoritmo]
                makespan_por_trens = dados_algo.groupby('num_trens')['makespan'].mean()
                ax2.plot(makespan_por_trens.index, makespan_por_trens.values, 
                        marker='s', label=algoritmo, linewidth=2)
        ax2.set_title('Makespan vs Número de Trens')
        ax2.set_xlabel('Número de Trens')
        ax2.set_ylabel('Makespan (minutos)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Análise por quilometragem
        ax3 = axes[1, 0]
        if 'quilometragem' in df.columns:
            for algoritmo in df['algoritmo'].unique():
                dados_algo = df[df['algoritmo'] == algoritmo]
                tempo_por_km = dados_algo.groupby('quilometragem')['tempo_execucao'].mean()
                ax3.plot(tempo_por_km.index, tempo_por_km.values, 
                        marker='^', label=algoritmo, linewidth=2)
        ax3.set_title('Tempo de Execução vs Quilometragem')
        ax3.set_xlabel('Quilometragem (km)')
        ax3.set_ylabel('Tempo de Execução (segundos)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Análise por intervalo de tempo
        ax4 = axes[1, 1]
        if 'intervalo' in df.columns:
            for algoritmo in df['algoritmo'].unique():
                dados_algo = df[df['algoritmo'] == algoritmo]
                tempo_por_intervalo = dados_algo.groupby('intervalo')['tempo_execucao'].mean()
                ax4.plot(tempo_por_intervalo.index, tempo_por_intervalo.values, 
                        marker='d', label=algoritmo, linewidth=2)
        ax4.set_title('Tempo de Execução vs Intervalo de Tempo')
        ax4.set_xlabel('Intervalo (minutos)')
        ax4.set_ylabel('Tempo de Execução (segundos)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('analise_por_categorias.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def gerar_relatorio_detalhado(self):
        """Gera relatório detalhado organizado por categorias"""
        df = pd.DataFrame(self.dados_consolidados)
        
        if df.empty:
            return "Nenhum dado encontrado para análise!"
        
        relatorio = []
        relatorio.append("=" * 100)
        relatorio.append("RELATÓRIO COMPLETO DE ANÁLISE DE RESULTADOS FERROVIÁRIOS")
        relatorio.append("Organização por Estações, Quilometragens e Minutos")
        relatorio.append("=" * 100)
        relatorio.append("")
        
        # Resumo executivo
        relatorio.append("RESUMO EXECUTIVO")
        relatorio.append("-" * 50)
        relatorio.append(f"Total de cenários analisados: {len(df)}")
        relatorio.append(f"Algoritmos testados: {', '.join(df['algoritmo'].unique())}")
        relatorio.append(f"Distribuições testadas: {', '.join(df['distribuicao'].unique())}")
        relatorio.append("")
        
        # Análise por número de trens (estações)
        relatorio.append("ANÁLISE POR NÚMERO DE TRENS (ESTAÇÕES)")
        relatorio.append("-" * 50)
        
        trens_stats = df.groupby('num_trens').agg({
            'tempo_execucao': ['mean', 'std', 'count'],
            'makespan': ['mean', 'std'],
            'algoritmo': lambda x: x.value_counts().to_dict()
        }).round(3)
        
        for num_trens in sorted(df['num_trens'].unique()):
            dados_trens = df[df['num_trens'] == num_trens]
            tempo_medio = dados_trens['tempo_execucao'].mean()
            tempo_std = dados_trens['tempo_execucao'].std()
            count = len(dados_trens)
            
            relatorio.append(f"Trens: {num_trens}")
            relatorio.append(f"  - Cenários testados: {count}")
            relatorio.append(f"  - Tempo médio de execução: {tempo_medio:.3f} ± {tempo_std:.3f} segundos")
            
            if 'makespan' in dados_trens.columns and dados_trens['makespan'].notna().any():
                makespan_medio = dados_trens['makespan'].mean()
                relatorio.append(f"  - Makespan médio: {makespan_medio:.1f} minutos")
            
            # Contagem por algoritmo
            for algoritmo in dados_trens['algoritmo'].unique():
                count_algo = len(dados_trens[dados_trens['algoritmo'] == algoritmo])
                relatorio.append(f"  - {algoritmo}: {count_algo} cenários")
            relatorio.append("")
        
        # Análise por quilometragem
        if 'quilometragem' in df.columns:
            relatorio.append("ANÁLISE POR QUILOMETRAGEM")
            relatorio.append("-" * 50)
            
            for km in sorted(df['quilometragem'].unique()):
                dados_km = df[df['quilometragem'] == km]
                tempo_medio = dados_km['tempo_execucao'].mean()
                count = len(dados_km)
                
                relatorio.append(f"Quilometragem: {km} km")
                relatorio.append(f"  - Cenários testados: {count}")
                relatorio.append(f"  - Tempo médio de execução: {tempo_medio:.3f} segundos")
                
                for algoritmo in dados_km['algoritmo'].unique():
                    count_algo = len(dados_km[dados_km['algoritmo'] == algoritmo])
                    relatorio.append(f"  - {algoritmo}: {count_algo} cenários")
                relatorio.append("")
        
        # Análise por intervalo de tempo
        if 'intervalo' in df.columns:
            relatorio.append("ANÁLISE POR INTERVALO DE TEMPO")
            relatorio.append("-" * 50)
            
            for intervalo in sorted(df['intervalo'].unique()):
                dados_intervalo = df[df['intervalo'] == intervalo]
                tempo_medio = dados_intervalo['tempo_execucao'].mean()
                count = len(dados_intervalo)
                
                relatorio.append(f"Intervalo: {intervalo} minutos")
                relatorio.append(f"  - Cenários testados: {count}")
                relatorio.append(f"  - Tempo médio de execução: {tempo_medio:.3f} segundos")
                
                for algoritmo in dados_intervalo['algoritmo'].unique():
                    count_algo = len(dados_intervalo[dados_intervalo['algoritmo'] == algoritmo])
                    relatorio.append(f"  - {algoritmo}: {count_algo} cenários")
                relatorio.append("")
        
        # Comparação entre algoritmos
        relatorio.append("COMPARAÇÃO ENTRE ALGORITMOS")
        relatorio.append("-" * 50)
        
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
            relatorio.append(f"  - Total de cenários: {len(dados_algo)}")
            
            if 'makespan' in dados_algo.columns and dados_algo['makespan'].notna().any():
                makespan_medio = dados_algo['makespan'].mean()
                relatorio.append(f"  - Makespan médio: {makespan_medio:.1f} minutos")
            relatorio.append("")
        
        # Conclusões e recomendações
        relatorio.append("CONCLUSÕES E RECOMENDAÇÕES")
        relatorio.append("-" * 50)
        
        # Determinar algoritmo mais rápido
        tempo_por_algoritmo = df.groupby('algoritmo')['tempo_execucao'].mean()
        algoritmo_mais_rapido = tempo_por_algoritmo.idxmin()
        tempo_mais_rapido = tempo_por_algoritmo.min()
        
        relatorio.append(f"• Algoritmo mais rápido: {algoritmo_mais_rapido} ({tempo_mais_rapido:.3f}s)")
        
        # Análise de escalabilidade
        for algoritmo in df['algoritmo'].unique():
            dados_algo = df[df['algoritmo'] == algoritmo]
            if len(dados_algo) > 1:
                correlacao = dados_algo['num_trens'].corr(dados_algo['tempo_execucao'])
                relatorio.append(f"• {algoritmo}: Correlação trens vs tempo = {correlacao:.3f}")
        
        relatorio.append("")
        relatorio.append("RECOMENDAÇÕES:")
        relatorio.append("• Para problemas pequenos (1-3 trens): Ambos os algoritmos são adequados")
        relatorio.append("• Para problemas médios (4-6 trens): Considerar trade-off entre velocidade e qualidade")
        relatorio.append("• Para problemas grandes (7+ trens): Avaliar requisitos específicos de tempo vs qualidade")
        relatorio.append("• Quilometragens maiores tendem a aumentar o tempo de execução")
        relatorio.append("• Intervalos menores podem resultar em soluções mais complexas")
        
        return "\n".join(relatorio)
    
    def salvar_dados_organizados(self):
        """Salva os dados organizados em arquivos Excel"""
        df = pd.DataFrame(self.dados_consolidados)
        
        if df.empty:
            print("Nenhum dado para salvar!")
            return
        
        # Salvar dados consolidados
        with pd.ExcelWriter('dados_consolidados_completos.xlsx', engine='openpyxl') as writer:
            # Dados completos
            df.to_excel(writer, sheet_name='Dados_Completos', index=False)
            
            # Resumo por número de trens
            if not self.resultados_por_estacoes.empty:
                self.resultados_por_estacoes.to_excel(writer, sheet_name='Por_Estacoes')
            
            # Resumo por quilometragem
            if not self.resultados_por_km.empty:
                self.resultados_por_km.to_excel(writer, sheet_name='Por_Quilometragem')
            
            # Resumo por minutos
            if not self.resultados_por_minutos.empty:
                self.resultados_por_minutos.to_excel(writer, sheet_name='Por_Minutos')
        
        print("Dados salvos em 'dados_consolidados_completos.xlsx'")
    
    def executar_analise_completa(self):
        """Executa análise completa dos resultados"""
        print("Iniciando análise completa dos resultados...")
        
        # Coletar dados
        self.coletar_todos_dados()
        
        if not self.dados_consolidados:
            print("Nenhum dado encontrado para análise!")
            return
        
        # Gerar gráficos
        self.gerar_graficos_por_categorias()
        
        # Gerar relatório
        relatorio = self.gerar_relatorio_detalhado()
        
        # Salvar relatório
        with open('relatorio_analise_completa.txt', 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        # Salvar dados organizados
        self.salvar_dados_organizados()
        
        print("\nAnálise completa finalizada!")
        print("Arquivos gerados:")
        print("- relatorio_analise_completa.txt")
        print("- analise_por_categorias.png")
        print("- dados_consolidados_completos.xlsx")
        
        return relatorio

def main():
    """Função principal"""
    # Caminho do workspace
    workspace_path = "."
    
    # Criar analisador
    analisador = AnalisadorCompletoResultados(workspace_path)
    
    # Executar análise completa
    relatorio = analisador.executar_analise_completa()
    
    # Exibir resumo
    if relatorio:
        print("\n" + "="*100)
        print("RESUMO DA ANÁLISE")
        print("="*100)
        print(relatorio)

if __name__ == "__main__":
    main()
