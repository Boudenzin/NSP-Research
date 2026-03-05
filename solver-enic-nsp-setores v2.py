from pulp import *
import random

# ==============================================================================
# 1. CONJUNTOS (DEFINIÇÃO DO ESPAÇO DO PROBLEMA)
# ==============================================================================
# Aqui definimos os domínios sobre os quais os índices (a, t, d) irão iterar.
avaliadores = [f"Prof_{i}" for i in range(1, 13)]  # Conjunto A (Avaliadores - 12 Avaliadores) 
dias = [1, 2, 3, 4]                               # Conjunto D (Dias do Evento - 4 Dias)
turnos = [1, 2, 3]                                # Conjunto T (1=Manhã, 2=Tarde, 3=Noite)
setores = [1, 2, 3, 4]                              # Conjunto S (1=Exatas, 2=Humanas, 3=Saúde, 4=Tecnologia)

# ==============================================================================
# 2. PARÂMETROS E PESOS (DADOS DE ENTRADA)
# ==============================================================================
# r_tds: Demanda por turno, dia e área. 
# Exemplo: Dia 1, Turno 1 (Manhã) precisa de 1 de Exatas, 1 de Humanas e 1 de Saúde.
# Zerando a demanda para limpar o cenário anterior
r = {(t, d, s): 0 for t in turnos for d in dias for s in setores}

# O GARGALO: Dia 3 está lotado de Saúde e Tecnologia
r[1, 3, 3] = 3  # Manhã do Dia 3: Precisa de 3 profs de Saúde
r[1, 3, 4] = 2  # Manhã do Dia 3: Precisa de 2 profs de Tecnologia
r[2, 3, 3] = 2  # Tarde do Dia 3: Precisa de 2 profs de Saúde
r[2, 3, 4] = 3  # Tarde do Dia 3: Precisa de 3 profs de Tecnologia

# h_as: Matriz de Habilidade (1 se o prof a domina a área s)
# Vamos inicializar todos como 0 e dar habilidades específicas
h = {(a, s): 0 for a in avaliadores for s in setores}
for a in avaliadores:
    # Exemplo: Professores ímpares são de Exatas(1)/Tec(4), pares são Humanas(2)/Saúde(3)
    if int(a.split('_')[1]) % 2 != 0:
        h[a, 1] = 1
        h[a, 4] = 1
    else:
        h[a, 2] = 1
        h[a, 3] = 1

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

# Supondo que Prof_2 e Prof_4 são seus únicos especialistas de Saúde/Tec
p["Prof_2", 1, 3] = 0  # Prof_2 indisponível na Manhã do Dia 3
p["Prof_4", 1, 3] = 0  # Prof_4 indisponível na Manhã do Dia 3

# Forçar especialistas a trabalhar na noite anterior (Dia 2, Turno 3)
r[3, 2, 3] = 2 # Demanda de Saúde na noite anterior
r[3, 2, 4] = 2 # Demanda de Tecnologia na noite anterior

# ==============================================================================
# 3. CRIAÇÃO DO MODELO MATEMÁTICO (OBJETO DO PROBLEMA)
# ==============================================================================
# Definimos que o problema é de Maximizar a satisfação total (Z).
prob = LpProblem("Escalonamento_ENIC_V2", LpMaximize)

# ==============================================================================
# 4. VARIÁVEIS DE DECISÃO (O QUE O MODELO DEVE DECIDIR)
# ==============================================================================
# x[a][t][d][s] é a nossa variável binária {0, 1}. 
# No Python, criamos um dicionário que mapeia cada combinação (a, t, d, s).
x = LpVariable.dicts("x", (avaliadores, turnos, dias, setores), cat="Binary")

# ==============================================================================
# 5. FUNÇÃO OBJETIVO: MAX Z = Σ p_atd * x_atds
# ==============================================================================
# O objetivo é maximizar o somatório dos pesos das escolhas feitas.
prob += lpSum(p[a, t, d] * x[a][t][d][s] for a in avaliadores for t in turnos for d in dias for s in setores), "Satisfacao_Total"

# ==============================================================================
# 6. RESTRIÇÕES (AS REGRAS QUE LIMITAM O SISTEMA)
# ==============================================================================

# I. COBERTURA POR ÁREA: Σ a∈A (x_atds) = r_tds
for d in dias:
    for t in turnos:
        for s in setores:
            prob += lpSum(x[a][t][d][s] for a in avaliadores) == r[t, d, s]

# II. EXCLUSIVIDADE DIÁRIA E ÚNICA ÁREA: Σ t,s (x_atds) <= 1
for a in avaliadores:
    for d in dias:
        prob += lpSum(x[a][t][d][s] for t in turnos for s in setores) <= 1

# III. DESCANSO NOTURNO (ZUMBI): Σs x_a3ds + Σs x_a1(d+1)s <= 1
for a in avaliadores:
    for d in dias[:-1]:
        prob += lpSum(x[a][3][d][s] for s in setores) + lpSum(x[a][1][d+1][s] for s in setores) <= 1

# IV. CARGA MÁXIMA E FOLGA: Σ t,d,s (x_atds) <= ca_valor
for a in avaliadores:
    prob += lpSum(x[a][t][d][s] for t in turnos for d in dias for s in setores) <= ca_valor

# V. HABILIDADE: x_atds <= h_as (SÓ ALOCA SE TIVER COMPETÊNCIA)
for a in avaliadores:
    for t in turnos:
        for d in dias:
            for s in setores:
                prob += x[a][t][d][s] <= h[a, s]

# ==============================================================================
# 7. RESOLUÇÃO E EXIBIÇÃO DE RESULTADOS
# ==============================================================================

# Aqui é só configuração de como o solver deve mostrar os resultados.
status = prob.solve()

if LpStatus[status] == 'Optimal':
    print(f"Status: {LpStatus[status]}")
    for d in dias:
        print(f"\n--- DIA {d} ---")
        for t in turnos:
            nome_t = {1:"MANHÃ", 2:"TARDE", 3:"NOITE"}[t]
            print(f"  {nome_t}:")
            for s in setores:
                nome_s = {1:"Exatas", 2:"Humanas", 3:"Saúde", 4:"Tecnologia"}[s]
                escolhidos = [a for a in avaliadores if value(x[a][t][d][s]) == 1]
                if escolhidos:
                    print(f"    [{nome_s}]: {', '.join(escolhidos)}")
else:
    print("Inviável: Verifique se a demanda r_tds não supera a oferta de profs por área.")