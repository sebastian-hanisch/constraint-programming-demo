"""Ruft den echten Google-OR-Tools-CP-SAT-Solver auf derselben Instanz auf - bereits
etablierte Portfolio-Abhängigkeit (quaycrane-demo, berth-allocation-demo), hier zum
ersten Mal in der Konzepte-Reihe. Dient als unabhängiger Korrektheits-Cross-Check UND
als Beleg, wie ein echter industrieller Solver an dieselbe Aufgabe herangeht - mit
weit ausgefeilterer Propagation und gelernten Klauseln, hier nur an Ergebnis/Zeit
demonstriert, nicht Schritt für Schritt visualisiert."""

from ortools.sat.python import cp_model

from csp_constants import ORTOOLS_TIME_LIMIT_SECONDS


def solve_with_ortools(instance, time_limit_seconds=ORTOOLS_TIME_LIMIT_SECONDS):
    model = cp_model.CpModel()
    n = instance.n_items
    x = [model.NewBoolVar(f"x{i}") for i in range(n)]

    model.Add(sum(instance.weights[i] * x[i] for i in range(n)) <= instance.capacity)
    for i, j in instance.incompatible_pairs:
        model.Add(x[i] + x[j] <= 1)
    model.Maximize(sum(instance.values[i] * x[i] for i in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 1  # ein Kern, deterministisch - fairer Vergleich

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        best_value = int(round(solver.ObjectiveValue()))
        selection = tuple(bool(solver.Value(xi)) for xi in x)
    else:
        best_value = None
        selection = None

    return {
        "status": solver.StatusName(status),
        "proven_optimal": status == cp_model.OPTIMAL,
        "best_value": best_value,
        "selection": selection,
        "wall_time": solver.WallTime(),
    }
