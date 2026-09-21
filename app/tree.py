"""Build a hierarchical tree structure (for D3) from people + relationships."""
from app import repository


def build_tree_data() -> dict:
    """Return nodes + links in a format D3 force-graph can consume.

    nodes: [{id, name, dob, dod, gender, photo_url}]
    links: [{source, target, type}]  type: 'parent' | 'spouse'
    """
    people = repository.list_people()
    relationships = repository.list_relationships()

    nodes = [
        {
            "id": p["id"],
            "name": f"{p['first_name']} {p['last_name'] or ''}".strip(),
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "dob": p["dob"],
            "dod": p["dod"],
            "gender": p["gender"],
            "photo_url": p["photo_url"],
            "notes": p["notes"],
        }
        for p in people
    ]

    links = [
        {
            "source": r["person_a_id"],
            "target": r["person_b_id"],
            "type": r["relationship_type"],
        }
        for r in relationships
    ]

    return {"nodes": nodes, "links": links}
