from pulp import *
import random

# ==============================================================================
# 1. CONJUNTOS (DEFINIÇÃO DO ESPAÇO DO PROBLEMA)
# ==============================================================================
# Aqui definimos os domínios sobre os quais os índices (a, t, d) irão iterar.
avaliadores = [f"Prof_{i}" for i in range(1, 13)]  # Conjunto A (Avaliadores - 12 Avaliadores) 
dias = [1, 2, 3, 4]                               # Conjunto D (Dias do Evento - 4 Dias)
turnos = [1, 2, 3]                                # Conjunto T (1=Manhã, 2=Tarde, 3=Noite)

# ==============================================================================
# 2. PARÂMETROS E PESOS (DADOS DE ENTRADA)
# ==============================================================================
# r_t: Demanda de cobertura para cada turno t em T
# (Manhã: 3, Tarde: 3, Noite: 2)
r = {1: 3, 2: 3, 3: 2} 

# c_a: Carga máxima de turnos (Total de dias - 1 para garantir folga)
ca_valor = len(dias) - 1

# p_atd: Coeficientes de Preferência (Pesos da Função Objetivo)
# Inicializamos todos com peso 5 (neutro)
p = {(a, t, d): 5 for a in avaliadores for t in turnos for d in dias}

# Aqui nesse caso, pra testar as preferências, foram pensados em 3 professores que tem 
# preferências especificas.

# Usei a seguinte escala de peso.
# 0 = Indisponivel, não pode estar lá
# 1 = Última opção, ele está disponível, mas não quer ir naquele dia.
# 5 = Está disponível normalmente
# 9 = Tem forte preferência por aquele dia.

# Exemplo 1: Prof_1 tem alta preferência pela manhã (Peso 9) e detesta a noite (Peso 1)
for d in dias:
    p["Prof_1", 1, d] = 9
    p["Prof_1", 3, d] = 1

# Exemplo 2: Prof_2 não pode trabalhar no Dia 1 (Peso 0 = Indisponibilidade)
for t in turnos:
    p["Prof_2", t, 1] = 0

# Exemplo 3: Prof_3 adora o turno da noite (Peso 9)
for d in dias:
    p["Prof_3", 3, d] = 9

# ==============================================================================
# 3. CRIAÇÃO DO MODELO MATEMÁTICO (OBJETO DO PROBLEMA)
# ==============================================================================
# Definimos que o problema é de Maximizar a satisfação total (Z).
prob = LpProblem("Escalonamento_ENIC_UFPB", LpMaximize)

# ==============================================================================
# 4. VARIÁVEIS DE DECISÃO (O QUE O MODELO DEVE DECIDIR)
# ==============================================================================
# x[a][t][d] é a nossa variável binária {0, 1}. 
# No Python, criamos um dicionário que mapeia cada combinação (a, t, d).
x = LpVariable.dicts("x", (avaliadores, turnos, dias), cat="Binary")

# ==============================================================================
# 5. FUNÇÃO OBJETIVO: MAX Z = Σ p_atd * x_atd
# ==============================================================================
# O objetivo é maximizar o somatório dos pesos das escolhas feitas.
prob += lpSum(p[a, t, d] * x[a][t][d] for a in avaliadores for t in turnos for d in dias), "Satisfacao_Total"

# ==============================================================================
# 6. RESTRIÇÕES (AS REGRAS QUE LIMITAM O SISTEMA)
# ==============================================================================

# I. COBERTURA: Σ a∈A (x_atd) = r_t, ∀t, d
# Garante que a demanda de professores por turno seja exatamente preenchida.
for d in dias:
    for t in turnos:
        prob += lpSum(x[a][t][d] for a in avaliadores) == r[t], f"Cobertura_T{t}_D{d}"

# II. EXCLUSIVIDADE DIÁRIA: Σ t∈T (x_atd) <= 1, ∀a, d
# Impede que o mesmo professor trabalhe em dois turnos no mesmo dia.
for a in avaliadores:
    for d in dias:
        prob += lpSum(x[a][t][d] for t in turnos) <= 1, f"Um_Turno_Por_Dia_{a}_D{d}"

# III. DESCANSO NOTURNO: x_a,3,d + x_a,1,d+1 <= 1, ∀a, d < |D|
# Se trabalhar na Noite (3), não pode trabalhar na Manhã (1) do dia seguinte.
for a in avaliadores:
    for d in dias[:-1]:
        prob += x[a][3][d] + x[a][1][d+1] <= 1, f"Zumbi_Avoider_{a}_D{d}"

# IV. FOLGA OBRIGATÓRIA: Σ t,d (x_atd) <= |D| - 1, ∀a
# Garante que cada professor tenha ao menos um dia de folga total.
for a in avaliadores:
    prob += lpSum(x[a][t][d] for t in turnos for d in dias) <= ca_valor, f"Carga_Max_Folga_{a}"

# ==============================================================================
# 7. RESOLUÇÃO E EXIBIÇÃO DE RESULTADOS
# ==============================================================================

# Aqui é só configuração de como o solver deve mostrar os resultados.
status = prob.solve()

if LpStatus[status] == 'Optimal':
    print(f"Status da Solução: {LpStatus[status]} (Z máximo encontrado!)")
    
    # Organização visual para o relatório
    for d in dias:
        print(f"\n[ DIA {d} ]")
        for t in turnos:
            nome_turno = {1: "MANHÃ", 2: "TARDE", 3: "NOITE"}[t]
            # Filtramos quem foi escolhido (x=1)
            escolhidos = [a for a in avaliadores if value(x[a][t][d]) == 1]
            print(f"  {nome_turno}: {', '.join(escolhidos)}")
else:
    print("ERRO: A instância é inviável com as restrições atuais.")