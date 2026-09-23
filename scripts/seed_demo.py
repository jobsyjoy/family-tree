"""Populate the database with a small demo family.

Handy for kicking the tyres before entering real relatives.
Run from the project root:  .venv\\Scripts\\python.exe -m scripts.seed_demo
"""
from app.database import init_db
from app import repository

FAMILY = [
    # (key, fields)
    ("grandpa", {"first_name": "Arthur", "last_name": "Hale", "nickname": "Art",
                 "dob": "1938-04-02", "dod": "2016-11-30", "gender": "male",
                 "birth_place": "Leeds, UK", "occupation": "Railway engineer",
                 "education": "Leeds Technical College",
                 "fun_fact": "Could whistle two notes at once.",
                 "notes": "Built the garden shed that still stands today."}),
    ("grandma", {"first_name": "Mary", "last_name": "Hale", "nickname": "Mim",
                 "dob": "1941-08-19", "gender": "female", "birth_place": "York, UK",
                 "occupation": "Primary school teacher",
                 "fun_fact": "Has never lost a game of Scrabble."}),
    ("dad", {"first_name": "Peter", "last_name": "Hale", "dob": "1968-01-15",
             "gender": "male", "birth_place": "Leeds, UK", "occupation": "Architect",
             "education": "University of Manchester",
             "fun_fact": "Ran the London Marathon in 1999."}),
    ("mum", {"first_name": "Susan", "last_name": "Hale", "dob": "1970-06-23",
             "gender": "female", "birth_place": "Bristol, UK",
             "occupation": "Nurse practitioner",
             "fun_fact": "Speaks fluent Welsh."}),
    ("aunt", {"first_name": "Clare", "last_name": "Hale", "dob": "1972-03-11",
              "gender": "female", "occupation": "Marine biologist",
              "fun_fact": "Has swum with whale sharks."}),
    ("kid1", {"first_name": "Ella", "last_name": "Hale", "dob": "1998-09-05",
              "gender": "female", "occupation": "Product designer",
              "education": "Central Saint Martins",
              "fun_fact": "Climbs competitively."}),
    ("kid2", {"first_name": "Tom", "last_name": "Hale", "dob": "2001-12-20",
              "gender": "male", "occupation": "Software engineer",
              "fun_fact": "Makes his own hot sauce."}),
    ("kid3", {"first_name": "Rowan", "last_name": "Hale", "dob": "2024-02-14",
              "gender": "other", "notes": "Newest member of the family!"}),
]

SPOUSES = [("grandpa", "grandma"), ("dad", "mum")]
PARENTS = [
    ("grandpa", "dad"), ("grandma", "dad"),
    ("grandpa", "aunt"), ("grandma", "aunt"),
    ("dad", "kid1"), ("mum", "kid1"),
    ("dad", "kid2"), ("mum", "kid2"),
    ("kid1", "kid3"),
]


def main() -> None:
    init_db()
    if repository.list_people():
        print("Database already has people in it - skipping seed.")
        print("Delete data/family.db first if you want a clean demo.")
        return

    ids = {key: repository.create_person(fields) for key, fields in FAMILY}
    for a, b in SPOUSES:
        repository.create_relationship(ids[a], ids[b], "spouse")
    for parent, child in PARENTS:
        repository.create_relationship(ids[parent], ids[child], "parent")

    print(f"Seeded {len(ids)} people and "
          f"{len(SPOUSES) + len(PARENTS)} relationships across 4 generations.")


if __name__ == "__main__":
    main()
