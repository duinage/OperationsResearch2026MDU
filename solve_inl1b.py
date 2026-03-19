# Code solution for Assignment INL1 B
# author: Vadym Tunik
# use "pip install gurobipy" in terminal to install gurobipy library
import gurobipy as g

### DATA ###
blocks = list(range(1, 13))
districts = [1, 2, 3]
k = 3
n = len(blocks)
epsilon = 0.10

pop = {1: 850, 2: 920, 3: 780, 4: 1100, 
       5: 950, 6: 870, 7: 1050, 8: 800, 
       9: 1000, 10: 930, 11: 760, 12: 990}

votes_red = {1: 420, 2: 300, 3: 510, 4: 200, 5: 600, 6: 390, 
             7: 480, 8: 350, 9: 700, 10: 410, 11: 620, 12: 480}
votes_blue = {1: 380, 2: 580, 3: 240, 4: 860, 5: 310, 6: 450, 
              7: 540, 8: 420, 9: 270, 10: 490, 11: 120, 12: 480}

edges = [(1,2), (2,3), (3,4), (5,6), (6,7), (7,8), (9,10), (10,11), (11,12),
         (1,5), (2,6), (3,7), (4,8), (5,9), (6,10), (7,11), (8,12)]

dir_edges = []
for u, v in edges:
    dir_edges.extend([(u,v), (v,u)])

neighbors = {b: [] for b in blocks}
for u, v in dir_edges:
    neighbors[u].append(v)

total_pop = sum(pop.values())
avg_pop = total_pop / k
min_pop = avg_pop * (1 - epsilon)
max_pop = avg_pop * (1 + epsilon)

M = sum(max(0, votes_blue[b] - votes_red[b]) for b in blocks) + 1


### SOLVE ###
with g.Model("Gerrymandering") as m:
    ## vars ##
    # x[b, d] = 1 if block b is in district d
    x = m.addVars(blocks, districts, vtype=g.GRB.BINARY, name="x")

    # w[d] = 1 if Red wins district d
    w = m.addVars(districts, vtype=g.GRB.BINARY, name="w")

    # y[u, v] = 1 if adjacent blocks are in different districts
    y = m.addVars(edges, vtype=g.GRB.BINARY, name="y")

    # contiguity vars
    root = m.addVars(blocks, districts, vtype=g.GRB.BINARY, name="root")
    f = m.addVars(dir_edges, districts, vtype=g.GRB.CONTINUOUS, lb=0, name="f")

    ## objective ##
    m.setObjective(g.quicksum(y[u, v] for u, v in edges), g.GRB.MINIMIZE)

    ## constraints ##
    # C2: Complete assignment
    m.addConstrs((g.quicksum(x[b, d] for d in districts) == 1 for b in blocks), name="C2")

    # C3: Population balance
    for d in districts:
        dist_pop = g.quicksum(pop[b] * x[b, d] for b in blocks)
        m.addConstr(dist_pop >= min_pop, name=f"C3_min_d{d}")
        m.addConstr(dist_pop <= max_pop, name=f"C3_max_d{d}")

    # P1: Gerrymandering (Red must win at least (k+1)/2 = 2 districts)
    for d in districts:
        red_votes = g.quicksum(votes_red[b] * x[b, d] for b in blocks)
        blue_votes = g.quicksum(votes_blue[b] * x[b, d] for b in blocks)
        m.addConstr(red_votes >= blue_votes + 1 - M * (1 - w[d]), name=f"P1_win_d{d}")

    m.addConstr(g.quicksum(w[d] for d in districts) >= (k + 1) / 2, name="P1_majority")

    # P2: Compactness linking constraints (applies to both directions)
    for d in districts:
        for u, v in edges:
            m.addConstr(y[u, v] >= x[u, d] - x[v, d], name=f"P2_link1_{u}_{v}_d{d}")
            m.addConstr(y[u, v] >= x[v, d] - x[u, d], name=f"P2_link2_{u}_{v}_d{d}")

    # C4: Contiguity - One root per district
    for d in districts:
        m.addConstr(g.quicksum(root[b, d] for b in blocks) == 1, name=f"C4_one_root_d{d}")

    # C4: Contiguity - Root must be in district
    for b in blocks:
        for d in districts:
            m.addConstr(root[b, d] <= x[b, d], name=f"C4_root_assign_{b}_d{d}")

    # C4: Contiguity - Flow capacities (Tight bounds)
    for d in districts:
        dist_size = g.quicksum(x[i, d] for i in blocks)
        for u, v in dir_edges:
            m.addConstr(f[u, v, d] <= (n - 1) * x[u, d], name=f"C4_cap1_{u}_{v}_d{d}")
            m.addConstr(f[u, v, d] <= dist_size - 1, name=f"C4_cap2_{u}_{v}_d{d}")
            
        # Root supply tight bound
        for b in blocks:
            m.addConstr(g.quicksum(f[b, v, d] for v in neighbors[b]) <= dist_size - 1, name=f"C4_supply_{b}_d{d}")

    # C4: Contiguity - Flow conservation
    for b in blocks:
        for d in districts:
            inflow = g.quicksum(f[u, b, d] for u in neighbors[b])
            outflow = g.quicksum(f[b, v, d] for v in neighbors[b])
            m.addConstr(inflow - outflow >= x[b, d] - n * root[b, d], name=f"C4_conserv_{b}_d{d}")

    # BONUS: Symmetry breaking
    root_idx = {d: g.quicksum(b * root[b, d] for b in blocks) for d in districts}
    for d in range(1, k):
        m.addConstr(root_idx[d] <= root_idx[d + 1] - 1, name=f"Bonus_symmetry_d{d}")

    ## optimize ##
    m.optimize()

    if m.status == g.GRB.OPTIMAL:
        print(f"\nOptimal Boundary Edges: {m.objVal:.0f}")
        
        for d in districts:
            assigned = [b for b in blocks if x[b, d].x > 0.5]
            winner = "Red" if w[d].x > 0.5 else "Blue"
            print(f"District {d}: Blocks {assigned} | Won by: {winner}")
    else:
        print("\nNo feasible solution found.")