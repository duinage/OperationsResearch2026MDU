# Code solution for Assignment INL1 A
# author: Vadym Tunik
# use "pip install gurobipy" in terminal to install gurobipy library
import gurobipy as g

### DATA ###
# variable names follow the notation from the report for better readability
i = {
    'Fertilizer A': 15.00,
    'Fertilizer B': 17.00,
    'Fertilizer C': 14.00
}
F = list(i.keys())

A = {
    'Chemical I': 2100.00,
    'Chemical II': 7900.00,
    'Chemical III': 7400.00,
    'Chemical IV': 8000.00,
    'Chemical V': 8900.00
}
C = list(A.keys())

a = {
    ('Fertilizer A', 'Chemical I'): 0.06, ('Fertilizer A', 'Chemical II'): 0.89, ('Fertilizer A', 'Chemical III'): 0.42, ('Fertilizer A', 'Chemical IV'): 0.56, ('Fertilizer A', 'Chemical V'): 0.09,
    ('Fertilizer B', 'Chemical I'): 0.92, ('Fertilizer B', 'Chemical II'): 0.70, ('Fertilizer B', 'Chemical III'): 0.60, ('Fertilizer B', 'Chemical IV'): 0.25, ('Fertilizer B', 'Chemical V'): 0.78,
    ('Fertilizer C', 'Chemical I'): 0.45, ('Fertilizer C', 'Chemical II'): 0.47, ('Fertilizer C', 'Chemical III'): 0.04, ('Fertilizer C', 'Chemical IV'): 0.90, ('Fertilizer C', 'Chemical V'): 0.51
}


### SOLVE ###
with g.Model("FertilizerManufacturing") as m:

    # decision vars
    x = m.addVars(F, lb=0.0, name='x')

    # objective
    m.setObjective(g.quicksum(i[f] * x[f] for f in F), g.GRB.MAXIMIZE)

    # constraint
    m.addConstrs((g.quicksum(a[f, c] * x[f] for f in F) <= A[c] for c in C), name="A")

    m.optimize()
    m.printAttr('x')