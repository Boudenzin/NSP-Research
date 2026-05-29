from pulp import *

# ==============================================================================
# 1. CONJUNTOS
# ==============================================================================
n_funcionarios = 10  # Ajuste conforme sua necessidade
funcionarios = [f"F_{i}" for i in range(1, n_funcionarios + 1)]
dias = list(range(1, 8)) 
turnos = [1, 2, 3] 

# ==============================================================================
# 2. PARÂMETROS
# ==============================================================================
# Demanda mínima: 4 pessoas por turno/dia
min_td = {(t, d): 4 for t in turnos for d in dias}

M = 2  # Máximo de turnos por dia
W = 5  # DIAS DE TRABALHO OBRIGATÓRIOS

# ==============================================================================
# 3. MODELO E VARIÁVEIS
# ==============================================================================
prob = LpProblem("Escala_5x2_Hibrida", LpMinimize)

x = LpVariable.dicts("x", (funcionarios, turnos, dias), cat="Binary")
y = LpVariable.dicts("y", (funcionarios, dias), cat="Binary")
z = LpVariable.dicts("z", (funcionarios, dias), cat="Binary")

# ==============================================================================
# 4. FUNÇÃO OBJETIVO (Híbrida)
# ==============================================================================
# Minimizamos o total de turnos, mas o peso principal está nas folgas e dias ativos
prob += lpSum(x[f][t][d] for f in funcionarios for t in turnos for d in dias)

# ==============================================================================
# 5. RESTRIÇÕES
# ==============================================================================

# I. COBERTURA MÍNIMA
for d in dias:
    for t in turnos:
        prob += lpSum(x[f][t][d] for f in funcionarios) >= min_td[t, d]

# II. VÍNCULO X -> Y E LIMITE DIÁRIO (M)
for f in funcionarios:
    for d in dias:
        # Pelo menos um turno deve ser trabalhado para o dia ser considerado ATIVO (y=1)
        prob += lpSum(x[f][t][d] for t in turnos) >= 0.1 * y[f][d]
        # O total de turnos no dia não pode passar de M e só existe se y=1
        prob += lpSum(x[f][t][d] for t in turnos) <= M * y[f][d]

# III. JORNADA SEMANAL RÍGIDA (W = 5 dias EXATAMENTE)
for f in funcionarios:
    prob += lpSum(y[f][d] for d in dias) == W

# IV. FOLGAS CONSECUTIVAS (Lógica Z)
for f in funcionarios:
    prob += lpSum(z[f][d] for d in dias) == 1
    for d in dias:
        d_prox = (d % 7) + 1
        prob += y[f][d] <= 1 - z[f][d]
        prob += y[f][d_prox] <= 1 - z[f][d]

# V. DESCANSO INTERJORNADA (ZUMBI)
for f in funcionarios:
    for d in dias:
        d_prox = (d % 7) + 1
        prob += x[f][3][d] + x[f][1][d_prox] <= 1

# ==============================================================================
# 6. RESOLUÇÃO E IMPRESSÃO FORMATADA
# ==============================================================================
status = prob.solve(PULP_CBC_CMD(msg=0))

if LpStatus[status] == 'Optimal':
    print(f"Status: {LpStatus[status]}\n")
    
    for f in funcionarios:
        print(f"Escala para {f}:")
        for d in dias:
            status_dia = "TRABALHO" if value(y[f][d]) == 1 else "FOLGA"
            
            # Coleta os turnos trabalhados no dia
            turnos_dia = [f"Turno {t}" for t in turnos if value(x[f][t][d]) == 1]
            lista_turnos = ", ".join(turnos_dia)
            
            print(f"  Dia {d}: {status_dia:9} - {lista_turnos}")
        print("-" * 40)
else:
    print("Inviável! A demanda exige mais funcionários do que os disponíveis respeitando a 5x2.")