"""Plotly-Suchbaum, Portierung von branch-bound-demo/bb_visualization.py. Bewusst
dieselben fünf Pruning-/Knoten-Status wie dort - kein eigener "durch Kompatibilität
unzulässig"-Status (siehe csp_solver.py's Modul-Docstring, warum das bei dieser
Suchreihenfolge unmöglich ist). Der Effekt der Kompatibilitätsregeln zeigt sich
stattdessen im Hovertext: wie viele Pakete die Propagation an JEDEM Knoten automatisch
mit-ausgeschlossen hat."""

STATUS_STYLE = {
    "root": {"color": "#14233B", "label": "Start"},
    "branch": {"color": "#1f77b4", "label": "Verzweigt (weiter untersucht)"},
    "prune_infeasible": {"color": "#9aa6ba", "label": "Gestutzt (Kapazität)"},
    "prune_bound": {"color": "#d68a2e", "label": "Gestutzt (kann nicht mehr verbessern)"},
    "leaf_new_best": {"color": "#2ca02c", "label": "Neue beste Lösung"},
    "leaf_not_best": {"color": "#c4cbd8", "label": "Vollständig, nicht besser"},
}
STATUS_ORDER = ["root", "branch", "prune_infeasible", "prune_bound", "leaf_new_best", "leaf_not_best"]


def _compute_layout(nodes):
    by_id = {n.id: n for n in nodes}
    children = {}
    for n in nodes:
        if n.parent_id is not None:
            children.setdefault(n.parent_id, []).append(n.id)

    x_of = {}
    next_leaf_slot = [0]

    def assign(node_id):
        kids = children.get(node_id, [])
        if not kids:
            x_of[node_id] = next_leaf_slot[0]
            next_leaf_slot[0] += 1
            return x_of[node_id]
        xs = [assign(k) for k in kids]
        x_of[node_id] = sum(xs) / len(xs)
        return x_of[node_id]

    assign(nodes[0].id)
    return {nid: (x_of[nid], -by_id[nid].depth) for nid in x_of}


def _node_label(node, instance):
    if node.status == "root":
        label = "Start<br>noch keine Entscheidung"
    else:
        item_no = node.item_index + 1
        weight, value = instance.weights[node.item_index], instance.values[node.item_index]
        decision_txt = (
            f"Paket {item_no} AUFGENOMMEN (w={weight}, v={value})" if node.decision else f"Paket {item_no} AUSGELASSEN"
        )
        label = f"{decision_txt}<br>Gewicht bisher: {node.weight} / {instance.capacity}<br>Wert bisher: {node.value}"

        if node.status == "prune_infeasible":
            label += "<br>Kapazität überschritten"
        elif node.status == "prune_bound" and node.detail is not None:
            label += f"<br>Erreichbar höchstens {node.detail} - kann bisherigen besten Fund nicht mehr übertreffen"

    if node.incompatibility_exclusions:
        names = ", ".join(f"Paket {i + 1}" for i in node.incompatibility_exclusions)
        label += f"<br>Automatisch ausgeschlossen (Kompatibilität): {names}"

    return label


def build_tree_figure(instance, result, step, render_cap):
    import plotly.graph_objects as go

    layout_nodes = list(result.nodes)[:render_cap]
    layout = _compute_layout(layout_nodes)
    nodes = [n for n in layout_nodes if n.id <= step]
    rendered_ids = {n.id for n in nodes}

    fig = go.Figure()

    edge_x, edge_y = [], []
    for n in nodes:
        if n.parent_id is not None and n.parent_id in rendered_ids:
            x0, y0 = layout[n.parent_id]
            x1, y1 = layout[n.id]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#c4cbd8", width=1.5), hoverinfo="skip", showlegend=False))

    for status in STATUS_ORDER:
        group = [n for n in nodes if n.status == status]
        if not group:
            continue
        style = STATUS_STYLE[status]
        xs = [layout[n.id][0] for n in group]
        ys = [layout[n.id][1] for n in group]
        texts = [_node_label(n, instance) for n in group]
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="markers", name=style["label"],
                marker=dict(size=11 if status != "leaf_new_best" else 15, color=style["color"],
                            line=dict(width=1, color="white"),
                            symbol="star" if status == "leaf_new_best" else "circle"),
                hovertext=texts, hoverinfo="text",
            )
        )

    fig.update_layout(
        template="plotly_white", height=460,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=40, l=10, r=10, b=10),
    )
    return fig
