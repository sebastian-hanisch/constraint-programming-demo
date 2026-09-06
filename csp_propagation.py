"""Constraint-Propagation bis zum Fixpunkt: aus einer teilweisen Zuweisung
`forced` (Paket-Index -> True/False) werden so viele weitere Pakete wie möglich
zwangsläufig festgelegt, bevor überhaupt weiterverzweigt wird.

Drei Regeln - bei diesem Restriktionstyp (nur Kapazität + "höchstens eines von
beiden") forcieren beide inhaltlichen Regeln ausschließlich auf False, nie auf
True, weshalb ein einziger Durchlauf durch beide Regeln bereits den Fixpunkt
erreicht (keine Kaskaden zwischen den Regeln möglich) - die Schleife bleibt trotzdem
stehen, um das ehrlich als Fixpunkt-Iteration zu benennen und robust gegenüber
künftigen Regeltypen (z. B. Implikationen wie "wenn A, dann auch B") zu sein, die
sehr wohl kaskadieren würden.

Gibt (forced, reason, detail, incompatibility_exclusions) zurück - reason ist None
bei Erfolg, sonst "capacity"/"bound" mit einem erklärenden `detail` (die
verbleibende erreichbare Summe). `incompatibility_exclusions` ist ein Tupel der
Pakete, die DIESER Aufruf per Kompatibilitätsregel automatisch ausgeschlossen hat -
KEIN "incompatibility"-Abbruchgrund: sobald ein Paket aufgenommen ist, schließt die
Regel seinen Partner sofort aus, bevor die Suche je versuchen könnte, beide
gleichzeitig auf True zu setzen. Ein Widerspruch ("beide gleichzeitig gewählt")
kann bei dieser Suchreihenfolge deshalb strukturell nie auftreten - siehe
csp_solver.py's Modul-Docstring und die "Mathematische Formulierung" in app.py."""


def propagate(instance, forced, best_value):
    forced = dict(forced)
    incompatibility_exclusions = []

    for i, j in instance.incompatible_pairs:
        if forced.get(i) is True and forced.get(j) is True:
            # Defensive Invariante, kein normaler Codepfad: bei include-vor-
            # exclude-Verzweigung mit sofortiger Propagation nach jeder
            # Entscheidung kann die Suche das nie herbeiführen (siehe Modul-
            # Docstring) - ein Verstoß hier deutet auf einen Aufrufer hin, der
            # `forced` unter Umgehung der Suche selbst konstruiert hat.
            raise AssertionError(
                f"propagate: Pakete {i} und {j} sind beide auf True gesetzt, obwohl sie ein "
                f"Kompatibilitätspaar bilden - bei normaler Suche unmöglich."
            )

    committed_weight = sum(instance.weights[i] for i, v in forced.items() if v)
    if committed_weight > instance.capacity:
        return forced, "capacity", None, ()

    changed = True
    while changed:
        changed = False

        for i in range(instance.n_items):
            if i in forced:
                continue
            if committed_weight + instance.weights[i] > instance.capacity:
                forced[i] = False
                changed = True

        for i, j in instance.incompatible_pairs:
            if forced.get(i) is True and j not in forced:
                forced[j] = False
                incompatibility_exclusions.append(j)
                changed = True
            elif forced.get(j) is True and i not in forced:
                forced[i] = False
                incompatibility_exclusions.append(i)
                changed = True

    committed_value = sum(instance.values[i] for i, v in forced.items() if v)
    remaining_potential = committed_value + sum(
        instance.values[i] for i in range(instance.n_items) if i not in forced
    )
    if remaining_potential <= best_value:
        return forced, "bound", remaining_potential, tuple(incompatibility_exclusions)

    return forced, None, None, tuple(incompatibility_exclusions)
