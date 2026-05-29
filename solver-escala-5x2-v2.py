from pulp import *

# ==============================================================================
# 1. CONJUNTOS
# ==============================================================================
n_funcionarios = 12 
funcionarios = [f"F_{i}" for i in range(1, n_funcionarios + 1)]
dias = list(range(1, 8)) # 1=Seg, 6=Sab, 7=Dom
turnos = [1, 2, 3] 

# ==============================================================================
# 2. PARÂMETROS
# ==============================================================================
min_td = {(t, d): 5 for t in turnos for d in dias} # Demanda de 5 por turno
M = 2  # Máx turnos/dia
W = 5  # Dias de trabalho/semana
peso_fds = 50 # Bônus para folga no sábado/domingo

# ==============================================================================
# 3. MODELO E VARIÁVEIS
# ==============================================================================
prob = LpProblem("Escala_5x2_FDS", LpMinimize)

x = LpVariable.dicts("x", (funcionarios, turnos, dias), cat="Binary")
y = LpVariable.dicts("y", (funcionarios, dias), cat="Binary")
z = LpVariable.dicts("z", (funcionarios, dias), cat="Binary")

# ==============================================================================
# 4. FUNÇÃO OBJETIVO: Custo de turnos - Bônus de folga no FDS
# ==============================================================================
custo_turnos = lpSum(x[f][t][d] for f in funcionarios for t in turnos for d in dias)
bonus_fds = lpSum(peso_fds * z[f][6] for f in funcionarios) # z[f][6] é folga Sab+Dom

prob += custo_turnos - bonus_fds

# ==============================================================================
# 5. RESTRIÇÕES
# ==============================================================================

for d in dias:
    for t in turnos:
        prob += lpSum(x[f][t][d] for f in funcionarios) >= min_td[t, d]

for f in funcionarios:
    for d in dias:
        # Garante que se y=1, tem que ter pelo menos 1 turno (evita dia 'fantasma')
        prob += lpSum(x[f][t][d] for t in turnos) >= 0.1 * y[f][d]
        prob += lpSum(x[f][t][d] for t in turnos) <= M * y[f][d]

# Jornada de exatamente 5 dias
for f in funcionarios:
    prob += lpSum(y[f][d] for d in dias) == W

# Folga consecutiva de 2 dias
for f in funcionarios:
    prob += lpSum(z[f][d] for d in dias) == 1
    for d in dias:
        d_prox = (d % 7) + 1
        prob += y[f][d] <= 1 - z[f][d]
        prob += y[f][d_prox] <= 1 - z[f][d]

# Descanso Zumbi
for f in funcionarios:
    for d in dias:
        d_prox = (d % 7) + 1
        prob += x[f][3][d] + x[f][1][d_prox] <= 1

# ==============================================================================
# 6. RESOLUÇÃO E IMPRESSÃO
# ==============================================================================
status = prob.solve(PULP_CBC_CMD(msg=0))

if LpStatus[status] == 'Optimal':
    print(f"Status: {LpStatus[status]}\n")
    for f in funcionarios:
        folga_fds = "SIM" if value(z[f][6]) == 1 else "NÃO"
        print(f"Escala para {f} (Folga FDS: {folga_fds}):")
        for d in dias:
            status_dia = "TRABALHO" if value(y[f][d]) == 1 else "FOLGA"
            turnos_dia = [f"T{t}" for t in turnos if value(x[f][t][d]) == 1]
            print(f"  Dia {d}: {status_dia:9} - {', '.join(turnos_dia)}")
        print("-" * 45)
else:
    print("Inviável! A demanda de fim de semana impede que todos folguem juntos.")