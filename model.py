import math
from gurobipy import Model, GRB, quicksum

def optimize_model(N, C1, C2, C3, fc, gc, hc, theta, r, TC, TB, Ttol, epsilon, w, OB, OE, observed_days, d, a, Tij, V_kt):
    # Create a new model
    model = Model("EV Infrastructure Planning")

    # Decision variables
    A = model.addVars(N, range(1, C1+1), vtype=GRB.BINARY, name="A")
    B = model.addVars(N, range(1, C2+1), vtype=GRB.BINARY, name="B")
    O = model.addVars(N, range(1, C3+1), vtype=GRB.BINARY, name="O")
    L = model.addVars(N, vtype=GRB.BINARY, name="L")
    H = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="H")
    C = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="C")
    M = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="M")
    N_var = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="N")
    F = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="F")
    E = model.addVars(N, range(1, 25), vtype=GRB.INTEGER, name="E")
    D = model.addVars(N, N, range(1, 25), vtype=GRB.INTEGER, name="D")
    G = model.addVars(N, N, range(1, 25), vtype=GRB.INTEGER, name="G")
    I = model.addVars(N, vtype=GRB.INTEGER, name="I")

    # Objective function
    model.setObjective(
        quicksum(fc(c) * A[k, c] for k in N for c in range(1, C1+1)) +
        quicksum(gc(c) * B[k, c] for k in N for c in range(1, C2+1)) +
        quicksum(hc(c) * O[k, c] for k in N for c in range(1, C3+1)) +
        quicksum(w * d[i-1, j-1] * D[i, j, t] for i in N for j in N if i != j for t in range(OB, OE+1)) +
        quicksum(w * d[i-1, j-1] * G[i, j, t] for i in N for j in N if i != j for t in range(OB, OE+1)) +
        quicksum(theta * I[k] for k in N),
        GRB.MINIMIZE
    )

    # Constraints
    model.addConstrs((quicksum(A[k, c] for c in range(1, C1+1)) <= 1 for k in N), name="C2")
    model.addConstrs((quicksum(B[k, c] for c in range(1, C2+1)) <= 1 for k in N), name="C3")
    model.addConstrs((quicksum(O[k, c] for c in range(1, C3+1)) <= 1 for k in N), name="C4")
    model.addConstrs((L[k] <= quicksum(A[k, c] for c in range(1, C1+1)) + quicksum(B[k, c] for c in range(1, C2+1)) for k in N), name="C5")
    model.addConstrs((L[k] >= 0.5 * (quicksum(A[k, c] for c in range(1, C1+1)) + quicksum(B[k, c] for c in range(1, C2+1))) for k in N), name="C6")
    model.addConstrs((float(d[i-1, j-1]) <= r * (1 + quicksum(L[k] * int(a[i-1, j-1, k-1]) for k in N)) for i in N for j in N if i != j), name="C7")
    model.addConstrs((F[k, OB] == I[k] for k in N), name="C8")
    model.addConstrs((F[k, OE] == I[k] for k in N), name="C9")
    model.addConstrs((E[k, OB] == 0 for k in N), name="C10")

    model.addConstrs((
        F[k, t] == F[k, t-1] - H[k, t-1] + (M[k, t-TC] if t-TC >= 1 else 0) + (N_var[k, t-TC] if t-TC >= 1 else 0) -
        quicksum(D[k, j, t-1] for j in N if k != j) +
        quicksum(D[j, k, t-int(math.ceil(Tij[j-1, k-1]))] if t-int(math.ceil(Tij[j-1, k-1])) >= 1 else 0 for j in N if k != j)
        for k in N for t in range(OB, OE+1)
    ), name="C11")

    model.addConstrs((
        E[k, t] == E[k, t-1] + H[k, t-1] - M[k, t-1] - N_var[k, t-1] -
        quicksum(G[k, j, t-1] for j in N if k != j) +
        quicksum(G[j, k, t-int(math.ceil(Tij[j-1, k-1]))] if t-int(math.ceil(Tij[j-1, k-1])) >= 1 else 0 for j in N if k != j)
        for k in N for t in range(OB, OE+1)
    ), name="C12")

    model.addConstrs((M[k, t] + N_var[k, t] <= E[k, t] for k in N for t in range(OB, OE+1)), name="C13")
    model.addConstrs((quicksum(M[k, l] for l in range(max(1, t-TC+1), t+1)) <= quicksum(c * A[k, c] for c in range(1, C1+1)) for k in N for t in range(OB, OE+1)), name="C14")
    model.addConstrs((quicksum(N_var[k, l] for l in range(max(1, t-TC+1), t+1)) <= quicksum(c * O[k, c] for c in range(1, C3+1)) for k in N for t in range(OB, OE+1)), name="C15")
    model.addConstrs((H[k, t] <= (1/TB) * quicksum(c * B[k, c] for c in range(1, C2+1)) for k in N for t in range(OB, OE+1)), name="C16")

    model.addConstrs((quicksum(D[k, j, t] for j in N if k != j) <= F[k, t] - H[k, t] for k in N for t in range(OB, OE+1)), name="C17")
    model.addConstrs((quicksum(G[k, j, t] for j in N if k != j) <= E[k, t] + H[k, t] for k in N for t in range(OB, OE+1)), name="C18")

    model.addConstrs((
        quicksum(F[k, t] + E[k, t] + quicksum(M[k, l] + N_var[k, l] for l in range(t-TC+1, t+1)) +
        quicksum(D[k, j, t-int(math.ceil(Tij[k-1, j-1]))] + G[k, j, t-int(math.ceil(Tij[k-1, j-1]))] if t-int(math.ceil(Tij[k-1, j-1])) >= 1 else 0 for j in N if k != j)
        for k in N) >= quicksum(I[k] for k in N)
        for t in range(OB, OE+1)
    ), name="C19")

    model.addConstrs((C[k, t] <= (quicksum(c * A[k, c] for c in range(1, C1+1)) - quicksum(M[k, l] for l in range(max(1, t-TC+1), t+1)) - quicksum(C[k, l] for l in range(max(1, t-TC), t)))
                    for k in N for t in range(OB, OE+1)), name="C20")

    model.addConstrs((C[k, t] + H[k, t] - float(1/Ttol) * L[k] >= float(V_kt[k-1,t-1]) for k in N for t in range(OB, OE+1)), name="C24")

    # Set variables to 0 outside of operational time
    for k in N:
        for t in range(1, 25):
            if t < OB or t > OE:
                model.addConstr(H[k, t] == 0)
                model.addConstr(C[k, t] == 0)
                model.addConstr(M[k, t] == 0)
                model.addConstr(N_var[k, t] == 0)
                model.addConstr(quicksum(D[k, j, t] for j in N if k != j) == 0)
                model.addConstr(quicksum(G[k, j, t] for j in N if k != j) == 0)

    model.Params.TimeLimit = 100  # Maximum running time in seconds
    model.Params.MIPGap = 0.01  # Relative optimality gap

    model.optimize()

    # Save results to a file
    with open("results.txt", "w") as f:
        if model.status == GRB.OPTIMAL:
            f.write("Optimal solution found!\n")
            f.write(f"Objective value: {model.ObjVal}\n")
            for v in model.getVars():
                if v.x > 0:
                    f.write(f"{v.varName}: {v.x}\n")
        else:
            f.write("No optimal solution found.\n")
            if model.status == GRB.INFEASIBLE:
                model.computeIIS()
                model.write("model.ilp")
                f.write("Model is infeasible. IIS written to 'model.ilp'\n")
                # Read and save the conflicting constraints
                with open("model.ilp", "r") as ilp_file:
                    for line in ilp_file:
                        f.write(line.strip() + "\n")