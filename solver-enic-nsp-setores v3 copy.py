from pulp import *

# ==============================================================================
# 1. CONJUNTOS
# ==============================================================================
n_avaliadores = 200 
avaliadores = [f"Prof_{i}" for i in range(1, n_avaliadores + 1)] 
dias = [1, 2, 3, 4] 
turnos = [1, 2, 3] 
setores = [1, 2, 3, 4] 

# ==============================================================================
# 2. PARÂMETROS E DEMANDA (AUMENTADA PARA GERAR STRESS)
# ==============================================================================
r = {(t, d, s): 0 for t in turnos for d in dias for s in setores}
r[1,1,2]=2; r[1,1,3]=1; r[2,1,1]=1; r[2,1,2]=2; r[2,1,3]=2; r[3,1,2]=1; r[3,1,3]=1
r[1,2,1]=1; r[1,2,2]=1; r[1,2,3]=1; r[1,2,4]=1; r[2,2,1]=1; r[2,2,2]=1; r[2,2,3]=1; r[2,2,4]=1; r[3,2,1]=1
r[1,3,1]=2; r[1,3,4]=2; r[2,3,1]=1; r[2,3,4]=2; r[3,3,1]=1; r[3,3,4]=1
r[1,4,2]=1; r[1,4,3]=1; r[2,4,1]=1; r[2,4,4]=1

# Multiplicando a demanda por 15 (aumentei de 10 para 15 para "apertar" o modelo)
for t in turnos:
    for d in dias:
        for s in setores:
            r[t, d, s] *= 15

h = {(a, s): 0 for a in avaliadores for s in setores}
for a in avaliadores:
    num = int(a.split('_')[1])
    if num % 2 != 0: 
        h[a, 1] = 1; h[a, 4] = 1
        if num > 15: h[a, 2] = 1 
    else: 
        h[a, 2] = 1; h[a, 3] = 1

p = {(a, t, d): 5 for a in avaliadores for t in turnos for d in dias}

# ==============================================================================
# 3. MODELO E VARIÁVEIS
# ==============================================================================
prob = LpProblem("ENIC_Equitativo", LpMaximize)
x = LpVariable.dicts("x", (avaliadores, turnos, dias, setores), cat="Binary")

# Variável auxiliar para penalizar quem trabalha demais (Min-Max simplificado)
# Queremos que a carga de todos fique próxima da média
carga_max = LpVariable("Carga_Maxima", lowBound=0, cat="Integer")

# ==============================================================================
# 4. FUNÇÃO OBJETIVO
# ==============================================================================
# Priorizamos as preferências, mas subtraímos um peso para manter a carga máxima baixa
# Isso força o modelo a distribuir os turnos em vez de dar 3 para um e 0 para outro.
preferencia = lpSum(p[a, t, d] * x[a][t][d][s] for a in avaliadores for t in turnos for d in dias for s in setores)
prob += preferencia - (100 * carga_max) 

# ==============================================================================
# 5. RESTRIÇÕES
# ==============================================================================

# I. COBERTURA
for d in dias:
    for t in turnos:
        for s in setores:
            prob += lpSum(x[a][t][d][s] for a in avaliadores) == r[t, d, s]

# II. EXCLUSIVIDADE DIÁRIA
for a in avaliadores:
    for d in dias:
        prob += lpSum(x[a][t][d][s] for t in turnos for s in setores) <= 1

# III. DESCANSO (ZUMBI)
for a in avaliadores:
    for d in dias[:-1]:
        prob += lpSum(x[a][3][d][s] for s in setores) + lpSum(x[a][1][d+1][s] for s in setores) <= 1

# IV. EQUIDADE (O CORAÇÃO DA MUDANÇA)
for a in avaliadores:
    total_trabalhado = lpSum(x[a][t][d][s] for t in turnos for d in dias for s in setores)
    
    # Todos devem trabalhar pelo menos 1 vez
    prob += total_trabalhado >= 1
    
    # Ninguém pode trabalhar mais que a variável carga_max
    # O otimizador vai tentar diminuir carga_max para ganhar pontos na função objetivo
    prob += total_trabalhado <= carga_max
    
    # Limite físico absoluto (opcional)
    prob += total_trabalhado <= 3

# V. HABILIDADE
for a in avaliadores:
    for t in turnos:
        for d in dias:
            for s in setores:
                prob += x[a][t][d][s] <= h[a, s]

# ==============================================================================
# 6. RESOLUÇÃO
# ==============================================================================
# Usando msg=1 para você ver o solver "suando" no console
status = prob.solve(PULP_CBC_CMD(msg=1))

if LpStatus[status] == 'Optimal':
    print(f"\nStatus: {LpStatus[status]}")
    print(f"Carga horária máxima atingida: {value(carga_max)} turnos")
    
    # Resumo rápido da carga para conferir a equidade
    cargas = [int(sum(value(x[a][t][d][s]) for t in turnos for d in dias for s in setores)) for a in avaliadores]
    print(f"Distribuição de cargas: Min {min(cargas)}, Max {max(cargas)}, Média {sum(cargas)/len(cargas):.2f}")
    
    # Exibir apenas os primeiros 10 para não lotar o terminal
    for a in avaliadores[:10]:
        carga = sum(value(x[a][t][d][s]) for t in turnos for d in dias for s in setores)
        print(f"{a:8}: {int(carga)} turnos")
else:
    print("Inviável! A demanda é maior do que a capacidade dos professores.")