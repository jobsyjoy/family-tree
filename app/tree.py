"""Turn people + relationships into graph data the front-end can draw.

A family "tree" is really a DAG (two parents per child, remarriages, etc.),
so we hand D3 nodes + links, plus a computed generation index that lets the
layered view stack people in tidy rows.
"""
from app import repository
from app.fields import FIELD_NAMES


def _display_name(person: dict) -> str:
    return f"{person['first_name']} {person.get('last_name') or ''}".strip()


def _generations(
    node_ids: list[int],
    parent_links: list[dict],
    spouse_links: list[dict],
) -> dict[int, int]:
    """Assign each person a generation depth: roots are 0, children deeper.

    Two rules, applied together until stable:
      1. A child sits at least one row below every parent (longest path, so
         both parents stay above their child).
      2. Spouses share a row -- otherwise someone who married in, and has no
         parents recorded, floats to the top of the chart away from partner.

    Cycles are capped rather than fatal; bad data shouldn't hang the page.
    """
    children: dict[int, list[int]] = {pid: [] for pid in node_ids}
    for link in parent_links:
        if link["source"] in children:
            children[link["source"]].append(link["target"])

    couples = [
        (link["source"], link["target"])
        for link in spouse_links
        if link["source"] in children and link["target"] in children
    ]

    depth = {pid: 0 for pid in node_ids}
    # Relaxing |nodes| times settles any acyclic graph; the cap stops a
    # malformed cycle from spinning forever.
    for _ in range(len(node_ids) + 1):
        changed = False
        for parent, kids in children.items():
            for kid in kids:
                if depth[kid] < depth[parent] + 1:
                    depth[kid] = depth[parent] + 1
                    changed = True
        for left, right in couples:
            deepest = max(depth[left], depth[right])
            if depth[left] != deepest or depth[right] != deepest:
                depth[left] = depth[right] = deepest
                changed = True
        if not changed:
            break
    return depth


def build_tree_data() -> dict:
    """Return {nodes, links} for the front-end renderers."""
    people = repository.list_people()
    relationships = repository.list_relationships()

    links = [
        {
            "source": r["person_a_id"],
            "target": r["person_b_id"],
            "type": r["relationship_type"],
        }
        for r in relationships
    ]
    parent_links = [link for link in links if link["type"] == "parent"]
    spouse_links = [link for link in links if link["type"] == "spouse"]
    depth = _generations([p["id"] for p in people], parent_links, spouse_links)

    nodes = []
    for person in people:
        node = {name: person.get(name) for name in FIELD_NAMES}
        node.update(
            id=person["id"],
            name=_display_name(person),
            generation=depth.get(person["id"], 0),
        )
        nodes.append(node)

    return {"nodes": nodes, "links": links}
