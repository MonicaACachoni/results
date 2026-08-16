# Comparativo CPLEX vs Java - Análise de Resultados

Este projeto contém um documento LaTeX que apresenta uma análise comparativa detalhada entre os resultados obtidos pelo solver CPLEX e pela implementação em Java para problemas de otimização ferroviária.

## Arquivos do Projeto

- `comparativo_cplex_java.tex` - Documento LaTeX principal
- `compilar_documento.py` - Script Python para compilar o documento
- `README.md` - Este arquivo de instruções

## Estrutura da Análise

O documento analisa os resultados considerando:

### Parâmetros de Teste
- **Distâncias**: 20km, 40km, 60km
- **Tempos limite**: 10min, 20min, 30min, 60min
- **Distribuições**: homo, normal, quase-normal
- **Complexidade**: 1c-1t a 8c-8t (combinações de carros e trens)

### Métricas Analisadas
- Tempo de execução
- Status da solução (ótima, viável, limite de tempo)
- Qualidade das soluções
- Escalabilidade
- Taxa de convergência

## Como Compilar o Documento

### Opção 1: Usando o Script Python

```bash
python compilar_documento.py
```

### Opção 2: Compilação Manual

```bash
pdflatex comparativo_cplex_java.tex
pdflatex comparativo_cplex_java.tex
```

### Requisitos

- LaTeX instalado (TeX Live, MiKTeX, ou similar)
- Python 3.x (para usar o script de compilação)

## Principais Conclusões

### CPLEX
- **Vantagens**: Garantia de otimalidade quando converge
- **Desvantagens**: Muitos cenários atingem limite de tempo
- **Escalabilidade**: Tempo cresce exponencialmente com complexidade

### Java
- **Vantagens**: Sempre retorna solução, tempo previsível
- **Desvantagens**: Não garante otimalidade
- **Escalabilidade**: Tempo cresce linearmente com complexidade

### Recomendações
- **Problemas pequenos**: CPLEX pode ser preferível
- **Problemas grandes**: Java é mais adequado
- **Ambiente de produção**: Java oferece maior confiabilidade

## Estrutura do Documento

1. **Introdução** - Contexto e objetivos
2. **Metodologia** - Configuração dos testes e métricas
3. **Análise dos Resultados** - Comparação detalhada
4. **Qualidade das Soluções** - Vantagens e desvantagens
5. **Escalabilidade** - Comportamento com aumento da complexidade
6. **Conclusões** - Principais descobertas e recomendações
7. **Apêndices** - Dados técnicos adicionais

## Dados Analisados

O documento foi baseado na análise dos seguintes tipos de arquivos:

### CPLEX
- Arquivos `.txt` com dados de execução
- Informações sobre tempo de execução
- Status da solução
- Valores das variáveis de decisão

### Java
- Arquivos de saída com cronogramas
- Tempo de execução do algoritmo
- Horários de partida e chegada dos trens

## Limitações

- Análise limitada aos cenários disponíveis
- Não foi possível avaliar detalhadamente a qualidade das soluções Java
- Resultados podem variar dependendo do hardware utilizado

## Trabalhos Futuros

1. Implementar métricas de qualidade para soluções Java
2. Expandir testes para cenários mais complexos
3. Análise de custo-benefício considerando licenças comerciais
4. Desenvolvimento de abordagem híbrida CPLEX-Java

## Contato

Para dúvidas ou sugestões sobre este documento, entre em contato através do sistema de controle de versão. 