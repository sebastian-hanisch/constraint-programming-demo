"""
Constraint Programming am Rucksackproblem – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der "Konzepte"-Reihe, Exakte-Suche-Linie - ein UNABHÄNGIGER Zweig ab
branch-bound-demo (nicht Fortsetzung/Kontrast/Konvergenz eines der anderen drei
Stücke): Constraint-Propagation statt LP-Schranken-Vergleich, dieselbe Rolle wie
gmm-demo/spectral-demo als unabhängige Zweige ab kmeans-demo in der Clustering-Linie.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import csp_constants as C
from csp_bruteforce import solve_bruteforce
from csp_evaluation import comparison, stats_up_to_step
from csp_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from csp_scenario import generate_instance
from csp_solver import solve
from csp_visualization import build_tree_figure

st.set_page_config(page_title="Constraint Programming – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_solve(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed):
    instance = generate_instance(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed)
    result = solve(instance)
    true_optimum, _true_selection = solve_bruteforce(instance)
    return instance, result, true_optimum


@st.cache_data(show_spinner=False)
def _compute_comparison(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed):
    instance = generate_instance(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed)
    result = solve(instance)
    return comparison(instance, result)


st.title("🧩 Constraint Programming am Rucksackproblem")
st.markdown(
    """
Ein **unabhängiger Zweig** der Exakte-Suche-Linie - keine Fortsetzung, kein Kontrast,
keine Konvergenz eines der anderen drei Stücke, sondern ein komplett anderer
Mechanismus für dasselbe Grundproblem: **Constraint-Propagation** verzweigt zwar auch
einen Suchbaum wie branch-bound-demo, aber statt eine LP-Schranke zu berechnen, wird
an jedem Knoten so viel wie möglich **logisch zwangsläufig festgelegt**, bevor
überhaupt weiterverzweigt wird. Genau **wie** das funktioniert, erklärt der
aufgeklappte Abschnitt direkt darunter.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren "
    "vergleichen, zeigt diese Demo - wie die übrigen Stücke der Exakte-Suche-Linie - ein "
    "wachsendes Beispiel. Das Vehikel-Problem ist hier erweitert: zusätzlich zum "
    "Gewichtslimit gibt es **Kompatibilitätsregeln** ('höchstens eines von zwei Paketen') "
    "- eine logische Nebenbedingung, die eine LP-Schranke (wie in branch-bound-demo) gar "
    "nicht ausdrücken kann."
)

with st.expander("So funktioniert Constraint Propagation", expanded=True):
    st.markdown(
        r"""
An jedem Suchbaum-Knoten wird **bis zum Fixpunkt propagiert**, bevor überhaupt eine
neue Entscheidung getroffen wird - drei Regeln, wiederholt bis nichts mehr passiert:

- **Kapazität**: würde ein noch offenes Paket das Gewichtslimit überschreiten (auf
  Basis der bereits aufgenommenen Pakete), wird es sofort auf "ausgeschlossen"
  festgelegt - auch wenn der Suchbaum es noch gar nicht "an der Reihe" hatte.
- **Kompatibilität** (die für dieses Stück namensgebende Regel): ist ein Paket
  aufgenommen und mit einem anderen inkompatibel, wird dieses andere sofort
  ausgeschlossen - **ohne** dass der Suchbaum diesen ganzen (zum Scheitern
  verurteilten) Ast je betreten müsste.

**Ein Ergebnis, das man zunächst nicht erwarten würde**: man könnte vermuten, eine
verletzte Kompatibilitätsregel liefert einen eigenen, sichtbaren Abbruchgrund im
Suchbaum ("dieser Ast ist durch eine Regel unzulässig"). Das kommt bei dieser
Suchreihenfolge nie vor - sobald ein Paket aufgenommen wird, schließt die Regel
seinen Partner sofort aus, **bevor** die Suche je versuchen könnte, beide
gleichzeitig zu wählen. Der Nutzen der Regel zeigt sich stattdessen daran, wie viele
Pakete auf dem Weg automatisch (mit-)ausgeschlossen wurden, ohne dass die Suche sie
einzeln ausprobieren musste - siehe die Kennzahl "Automatisch ausgeschlossen"
weiter unten und "📐 Mathematische Formulierung" für den Beweis.
- **Zielfunktion**: könnten selbst alle noch offenen Pakete zusammen den bisher
  besten Fund nicht mehr übertreffen, bricht der Ast ab - bewusst dieselbe
  **schwache** Formel wie branch-bound-demos `weak_bound`, damit jeder Unterschied
  in der Knotenzahl eindeutig der Propagation zuzuschreiben ist, nicht einer
  ohnehin schärferen Zahl.

**Ein struktureller Unterschied zu branch-bound-demo**: dort entspricht jede
Suchbaum-Ebene fest einem bestimmten Paket. Hier nicht - Propagation kann Pakete
"außer der Reihe" festlegen, die Suche wählt bei jedem Schritt einfach das nächste
noch UNENTSCHIEDENE Paket. Das ist der Grund, warum Kompatibilitätsverletzungen
sofort auffallen, statt erst am Ende eines langen, aussichtslosen Astes.

Zum Vergleich löst diese Demo dieselbe Instanz zusätzlich mit dem echten
**Google-OR-Tools-CP-SAT-Solver** - der Industriestandard, mit weit ausgefeilterer
Propagation und gelernten Klauseln, hier nur an Ergebnis und Zeit gezeigt, nicht
Schritt für Schritt.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Reines Rucksack (0 Regeln, Propagation hilft schon etwas)": "8 Pakete, keine Kompatibilitätsregeln - überraschend hilft Propagation trotzdem: Kapazitäts-Propagation schließt mehrere aussichtslose Pakete auf einen Schlag aus, statt sie einzeln auszuprobieren.",
    "Wenige Regeln, großer Unterschied": "Dieselbe Instanz, jetzt mit 3 Kompatibilitätsregeln - deutlich weniger Knoten als reines Branch & Bound auf demselben erweiterten Problem.",
    "Mehr Pakete, mehr Regeln": "14 Pakete, 5 Regeln - der Vorteil der Propagation wächst mit der Instanzgröße.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_items = st.slider("Anzahl Pakete", *bounds("n_items_slider"), key="n_items_slider")
    capacity_fraction = st.slider(
        "Gewichtslimit (Anteil der Gesamtmenge)", *bounds("capacity_fraction_slider"), key="capacity_fraction_slider"
    )
    correlation = st.slider(
        "Korrelation Wert/Gewicht", *bounds("correlation_slider"), key="correlation_slider",
        help="0 = Wert unabhängig vom Gewicht. 1 = wertvolle Pakete sind auch die schweren "
        "(branch-bound-demos Härtefall).",
    )
    n_incompatible_pairs = st.slider(
        "Anzahl Kompatibilitätsregeln", *bounds("n_incompatible_pairs_slider"), key="n_incompatible_pairs_slider",
        help="Jede Regel: 'Paket A und Paket B dürfen nicht beide gewählt werden.' Eine LP-Schranke "
        "(wie in branch-bound-demo) kann das nicht ausdrücken - Constraint-Propagation schon.",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        use_container_width=True,
        on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für Paketgewichte, -werte und Kompatibilitätsregeln.",
    )

sync_query_params(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed)

scenario_key = (int(n_items), capacity_fraction, correlation, int(n_incompatible_pairs), int(seed))

with st.spinner("Verzweige mit Propagation..."):
    instance, result, true_optimum = _compute_solve(*scenario_key)

if instance.incompatible_pairs:
    pairs_txt = ", ".join(f"P{i + 1}↔P{j + 1}" for i, j in instance.incompatible_pairs)
    st.caption(f"🔗 Kompatibilitätsregeln in dieser Instanz: {pairs_txt}")
else:
    st.caption("🔗 Keine Kompatibilitätsregeln in dieser Instanz (reines Rucksackproblem).")

st.markdown("## 🎯 Der Suchbaum mit Propagation")

if "csp_step" not in st.session_state or st.session_state.get("csp_step_owner") != scenario_key:
    st.session_state["csp_step"] = len(result.nodes) - 1
    st.session_state["csp_step_owner"] = scenario_key

max_step = len(result.nodes) - 1
step_col, play_col = st.columns([5, 1])
with step_col:
    if max_step == 0:
        step = 0
        st.caption("Nur der Wurzelknoten - kein Regler nötig.")
    else:
        step = st.slider(
            "Schritt (Knoten)", 0, max_step, key="csp_step",
            help="Ein Schritt = ein besuchter Suchbaum-Knoten, in Besuchsreihenfolge.",
        )
with play_col:
    auto_play = st.button("▶️ Abspielen", use_container_width=True)

render_note = (
    f" (zeigt die ersten {C.MAX_NODES_RENDERED:,} von {len(result.nodes):,} Knoten)"
    if len(result.nodes) > C.MAX_NODES_RENDERED
    else ""
)
st.caption(f"{len(result.nodes):,} Knoten insgesamt besucht{render_note}.")

tree_slot = st.empty()


def _render(current_step):
    tree_slot.plotly_chart(
        build_tree_figure(instance, result, current_step, C.MAX_NODES_RENDERED),
        use_container_width=True, key=f"tree_{current_step}",
    )


if auto_play:
    n_frames = min(max_step + 1, 60)
    frame_skip = max(1, (max_step + 1) // n_frames)
    for s in list(range(0, max_step, frame_skip)) + [max_step]:
        _render(s)
        time.sleep(0.08)
    step = max_step
else:
    _render(step)

live = stats_up_to_step(result, step)
lm1, lm2, lm3, lm4 = st.columns(4)
lm1.metric("Besuchte Knoten (bisher)", f"{live['nodes_so_far']:,}")
lm2.metric(
    "Gestutzt (Kapazität)", f"{live['pruned_infeasible']:,}",
    help="Ein noch offenes Paket wurde ausgeschlossen, weil es das Gewichtslimit überschritten hätte.",
)
lm3.metric(
    "Automatisch ausgeschlossen (Kompatibilität)", f"{live['incompatibility_exclusions']:,}",
    help="Pakete, die die Propagation automatisch mit-ausgeschlossen hat, weil ihr Partner aufgenommen wurde - "
    "ohne dass die Suche sie je einzeln ausprobieren musste. Genau das, was branch-bound-demos LP-Schranke "
    "nicht kann.",
)
lm4.metric(
    "Gestutzt (kann nicht mehr verbessern)", f"{live['pruned_bound']:,}",
    help="Selbst alle noch offenen Pakete zusammen reichen nicht mehr, um den bisher besten Fund zu übertreffen.",
)

if result.truncated:
    st.error(
        f"⛔ Abgebrochen bei {C.MAX_NODES_EXPLORED:,} untersuchten Knoten - das gezeigte Ergebnis ist die "
        f"beste bislang gefundene, nicht garantiert optimale Lösung."
    )
else:
    st.caption(
        f"Bewiesenes Optimum: **{result.best_value}** - stimmt mit der unabhängigen Bruteforce-Referenz überein."
        if result.best_value == true_optimum
        else f"⚠️ Optimum {result.best_value} weicht von der Bruteforce-Referenz {true_optimum} ab - bitte melden."
    )

st.markdown("---")

st.subheader("📐 Was bringt Constraint-Propagation wirklich?")
st.markdown(
    """
Live für Ihre aktuelle Instanz: dasselbe erweiterte Problem, einmal mit
Constraint-Propagation, einmal mit klassischem Branch & Bound (dieselbe schwache
Schranke wie branch-bound-demo, aber ohne jede Kompatibilitäts-Propagation -
Verletzungen fallen dort erst am Blatt auf), plus der echte OR-Tools-CP-SAT-Solver
als unabhängiger Beleg.
"""
)

cmp = _compute_comparison(*scenario_key)
cc1, cc2, cc3 = st.columns(3)
cc1.metric(
    "Diese Demo (Propagation)", f"{cmp['csp_nodes']:,} Knoten",
    help="Kompatibilitätsverletzungen werden sofort bei der Verzweigung erkannt, nicht erst am Blatt.",
)
cc2.metric(
    "Klassisches Branch & Bound", f"{cmp['bnb_nodes']:,} Knoten" + (" (abgebrochen)" if cmp["bnb_truncated"] else ""),
    delta=f"{cmp['bnb_nodes'] - cmp['csp_nodes']:,} ggü. Propagation", delta_color="inverse",
    help="Dieselbe schwache Bound-Formel wie branch-bound-demo, aber blind für Kompatibilitätsregeln - prüft "
    "sie erst am fertig entschiedenen Blatt.",
)
cc3.metric(
    "OR-Tools CP-SAT", cmp["ortools_best_value"],
    help=f"Echter industrieller Solver, {cmp['ortools_wall_time']:.4f}s - "
    + ("beweist Optimalität." if cmp["ortools_proven_optimal"] else "Zeitlimit erreicht."),
)

if cmp["csp_best_value"] == cmp["bnb_best_value"] == cmp["ortools_best_value"]:
    factor = cmp["bnb_nodes"] / cmp["csp_nodes"] if cmp["csp_nodes"] else float("inf")
    if factor >= 1.5:
        st.success(
            f"✅ Constraint-Propagation braucht **{factor:.1f}×** weniger Knoten als klassisches Branch & Bound "
            f"auf demselben erweiterten Problem - für dasselbe bewiesene Optimum. Alle drei Verfahren (diese "
            f"Demo, klassisches B&B, OR-Tools) finden denselben Wert: **{cmp['csp_best_value']}**."
        )
    else:
        st.info(
            "Bei dieser (kleinen oder regelarmen) Instanz ist der Unterschied noch nicht groß - mehr Pakete "
            "oder mehr Kompatibilitätsregeln machen ihn deutlicher (siehe Presets oben)."
        )
else:
    st.warning("⚠️ Die drei Verfahren sind sich uneinig - das sollte nie passieren, bitte melden.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Erweitertes 0/1-Rucksackproblem**: wie in branch-bound-demo, zusätzlich eine Menge
$P$ von Kompatibilitätspaaren - für jedes $(i,j) \in P$ gilt $x_i + x_j \le 1$
(höchstens eines von beiden).

**Propagation bis zum Fixpunkt**, ausgehend von einer Teilzuweisung (Paket-Index →
$\{0,1\}$ für bereits entschiedene Pakete, $F$ die Menge der entschiedenen Indizes):

$$
\begin{aligned}
&\textbf{Kapazität:} && \text{committed}_w + w_i > W \implies x_i \gets 0 \quad (i \notin F) \\
&\textbf{Kompatibilität:} && x_i = 1 \wedge (i,j) \in P \implies x_j \gets 0 \\
&\textbf{Zielfunktion:} && \text{committed}_v + \textstyle\sum_{i \notin F} v_i \le \text{bester Fund} \implies \text{Ast abbrechen}
\end{aligned}
$$

Wiederholt, bis sich nichts mehr ändert (Fixpunkt) - bei diesem Regeltyp (nur
Kapazität + paarweise Ausschlüsse) forcieren die ersten beiden Regeln ausschließlich
auf 0, nie auf 1, weshalb hier faktisch ein einziger Durchlauf genügt. Mit
Implikations-Regeln ("wenn A, dann auch B") würde das echt kaskadieren - bewusst
einfach gehalten, um bei diesem Stück den Kernunterschied (Propagation vs.
Bound-Vergleich) nicht zu verwässern.

**Warum "beide gleichzeitig gewählt" hier nie vorkommt**: das würde bedeuten, dass
für ein Paar $(i,j) \in P$ sowohl $x_i=1$ als auch $x_j=1$ von der Suche explizit
versucht werden. Sobald aber $x_i=1$ gesetzt wird, erzwingt die Kompatibilitätsregel
sofort $x_j \gets 0$ - noch bevor $j$ überhaupt wieder "an der Reihe" wäre. Die Suche
wählt bei jedem Schritt nur unter den noch UNENTSCHIEDENEN Paketen, $j$ ist zu
diesem Zeitpunkt aber bereits entschieden. Ein eigener "durch Kompatibilität
unzulässig"-Abbruch ist bei dieser Suchreihenfolge deshalb strukturell unmöglich -
der Nutzen der Regel liegt stattdessen darin, dass Pakete automatisch (mit-)
ausgeschlossen werden, ohne dass die Suche sie je einzeln ausprobieren muss (siehe
die Kennzahl "Automatisch ausgeschlossen" oben).

Implementiert in `csp_propagation.py` (die drei Regeln), `csp_solver.py`
(Tiefensuche mit dynamischer Variablenreihenfolge), `csp_bnb_reference.py`
(Vergleichs-B&B ohne Kompatibilitäts-Propagation) und `csp_ortools_reference.py`
(echter Google-OR-Tools-CP-SAT-Solver).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
