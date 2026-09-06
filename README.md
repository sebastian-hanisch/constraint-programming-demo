# Constraint Programming am Rucksackproblem – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-constraint-programming-demo.streamlit.app/)**

Fünftes Stück der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations
Research und Machine Learning", **Exakte-Suche-Linie** - ein **unabhängiger Zweig**
ab [branch-bound-demo](../branch-bound-demo): keine Fortsetzung, kein Kontrast (wie
[dynamic-programming-demo](../dynamic-programming-demo)), keine Konvergenz (wie
[branch-cut-demo](../branch-cut-demo)), sondern ein komplett anderer Mechanismus für
eine ANDERE Schwäche derselben Wurzel - dieselbe Rolle wie gmm-demo/spectral-demo als
unabhängige Zweige ab kmeans-demo in der Clustering-Linie.

## Warum das Vehikel-Problem erweitert ist

Reines 0/1-Rucksack hat nur eine Restriktion (Kapazität) - Constraint-Propagation
hätte dort wenig zu tun, und CP-SATs eigentliche Stärke (logische Nebenbedingungen,
die eine LP-Schranke gar nicht ausdrücken kann) käme nicht zur Geltung. Deshalb kommt
zur Kapazität eine kleine Anzahl zufälliger **Kompatibilitätsregeln** dazu: "Paket A
und Paket B dürfen nicht beide gewählt werden." branch-bound-demos LP-Schranke kann
das nicht ausdrücken und entdeckt eine Verletzung deshalb immer erst am Blatt -
Constraint-Propagation erkennt sie sofort bei der Verzweigung.

## Eine Überraschung beim Kalibrieren, nicht vorab angenommen

Selbst mit **0 Kompatibilitätsregeln** (reines Rucksack) braucht diese Demo bereits
spürbar weniger Knoten als klassisches Branch & Bound auf derselben Instanz (Faktor
~1,7× im Standard-Preset) - Kapazitäts-Propagation zwingt mehrere noch offene Pakete
auf einen Schlag auf "ausgeschlossen", sobald sie nicht mehr passen, während
klassisches B&B jedes einzeln ausprobieren muss. Kompatibilitätsregeln kommen in den
größeren Presets noch obendrauf (Faktor ~4,7× bzw. ~8,6×) - siehe
[tests/test_solver.py](tests/test_solver.py)s
`test_zero_incompatible_pairs_still_beats_bnb_reference_via_capacity_alone`.

## Ein zweiter Fund beim Kalibrieren: derselbe "unreachable status" wie branch-cut-demo

Der ursprüngliche Plan sah einen eigenen `prune_incompatible`-Knotenstatus vor ("dieser
Ast ist durch eine Kompatibilitätsregel unzulässig"). Live-Tests zeigten diesen Status
in JEDEM Preset bei 0 - genau wie [branch-cut-demo](../branch-cut-demo)s verworfener
`prune_cut`-Versuch, aber aus einem eigenen, strukturellen Grund: sobald ein Paket
aufgenommen wird, schließt die Kompatibilitätsregel dessen Partner SOFORT aus (noch
bevor die Suche ihn je "an der Reihe" hätte) - ein Widerspruch ("beide gleichzeitig
gewählt") kann bei dieser Suchreihenfolge deshalb nie explizit auftreten. Fix: der
Status wurde entfernt, `csp_propagation.propagate` prüft die Bedingung stattdessen als
`AssertionError`-Invariante (siehe `tests/test_propagation.py::
test_explicit_double_true_on_an_incompatible_pair_is_an_invariant_violation`), und
jeder Knoten trägt stattdessen `incompatibility_exclusions` - welche Pakete SEINE
EIGENE Propagation automatisch mit-ausgeschlossen hat. Kumuliert über den ganzen
Suchbaum ("Automatisch ausgeschlossen" in der App) ist das eine tatsächlich
beobachtbare, ehrliche Kennzahl für den Nutzen der Regel, statt eines nie auslösenden
Pruning-Grundes. Allgemeine Lehre (jetzt zweimal in Folge bestätigt): bei der
Komposition zweier Mechanismen nicht annehmen, dass ein plausibel klingender neuer
Fehlerfall auch wirklich eintritt - live nachmessen, bevor er in UI/Doku landet.

## Referenzlöser

- **`csp_bnb_reference.py`**: klassisches Branch & Bound auf demselben erweiterten
  Problem, mit branch-bound-demos eigener `weak_bound`-Formel (kennt die
  Kompatibilitätsregeln nicht - prüft sie erst am Blatt).
- **`csp_ortools_reference.py`**: der echte Google-OR-Tools-CP-SAT-Solver
  (bereits etablierte Portfolio-Abhängigkeit, hier zum ersten Mal in der
  Konzepte-Reihe) - unabhängiger Korrektheits-Cross-Check und Beleg, wie ein echter
  industrieller Solver an dieselbe Aufgabe herangeht.
- **`csp_bruteforce.py`**: vollständige Enumeration (prüft Kapazität UND
  Kompatibilität).

## Verifikation

- **Propagations-Invarianten**: kein Paket wird je gleichzeitig auf 0 und 1
  festgelegt; jede Verletzung (Kapazität, Zielfunktion) wird korrekt erkannt; ein
  künstlich herbeigeführter Kompatibilitäts-Widerspruch löst die `AssertionError`-
  Invariante aus, statt still ignoriert zu werden.
- **Ausschluss-Tracking**: `incompatibility_exclusions` ist über eine Mischung an
  Instanzen nachweislich manchmal > 0 (die Regel tut tatsächlich etwas), und kein
  Knoten trägt je den entfernten `prune_incompatible`-Status.
- **Bruteforce- und OR-Tools-Cross-Check**: `best_value` muss mit beiden
  unabhängigen Referenzen übereinstimmen.
- **Knotenzahl-Ordnung**: `csp_solver` braucht nie mehr Knoten als
  `csp_bnb_reference` auf derselben Instanz.
- **Sicherheitsgrenzen**: `MAX_NODES_EXPLORED` wird zuverlässig eingehalten.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, Suchbaum-Animation, Vergleich, Formulierungs-Expander |
| `csp_constants.py` | Defaults, Regler-Grenzen, Sicherheitsgrenzen, `PRESETS` |
| `csp_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `csp_scenario.py` | Zufällige Rucksack-Instanzen mit Kompatibilitätspaaren |
| `csp_propagation.py` | Die drei Propagationsregeln bis zum Fixpunkt |
| `csp_solver.py` | Tiefensuche mit dynamischer Variablenreihenfolge |
| `csp_bnb_reference.py` | Vergleichs-B&B ohne Kompatibilitäts-Propagation |
| `csp_ortools_reference.py` | Echter Google-OR-Tools-CP-SAT-Solver |
| `csp_bruteforce.py` | Unabhängige Referenzlösung (vollständige Enumeration) |
| `csp_evaluation.py` | Kennzahlen, Drei-Wege-Vergleich |
| `csp_visualization.py` | Suchbaum-Diagramm (Plotly), Ausschlüsse im Hovertext statt eigener Pruning-Farbe |
| `tests/` | Propagations-Invarianten, Bruteforce-/OR-Tools-Cross-Check, Knotenzahl-Ordnung, Ausschluss-Tracking, Sicherheitsgrenzen |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
