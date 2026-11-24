
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    path = DATA_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_course_catalog(data):
    catalog = {}

    sections = [
        "fixed_courses",
        "university_electives",
        "specialized_electives_list_1",
        "specialized_electives_list_2",
    ]

    for section in sections:
        for course in data.get(section, []):
            catalog[course["code"]] = course

    return catalog


def validate_prerequisites(catalog, prerequisites):
    errors = []
    relationship_list = []

    for prerequisite, dependents in prerequisites.items():

        # Check prerequisite existence
        if prerequisite not in catalog:
            errors.append(
                f"Unknown prerequisite course: {prerequisite}"
            )
            continue

        if not isinstance(dependents, list):
            errors.append(
                f"{prerequisite}: dependents must be a list"
            )
            continue

        for dependent in dependents:

            relationship = (prerequisite, dependent)
            relationship_list.append(relationship)

            # Check dependent existence
            if dependent not in catalog:
                errors.append(
                    f"Unknown dependent course: {dependent}"
                )
                continue

            # Check self-prerequisite
            if prerequisite == dependent:
                errors.append(
                    f"Self prerequisite detected: {prerequisite}"
                )

    # Check duplicate relationships
    counts = Counter(relationship_list)

    for relationship, count in counts.items():
        if count > 1:
            errors.append(
                f"Duplicate relationship: {relationship[0]} -> "
                f"{relationship[1]}"
            )

    return errors, relationship_list


def detect_cycles(catalog, prerequisites):
    # Convert prerequisite -> dependent into a graph
    graph = {
        code: []
        for code in catalog
    }

    for prerequisite, dependents in prerequisites.items():
        if prerequisite not in catalog or not isinstance(dependents, list):
            continue

        for dependent in dependents:
            if dependent in catalog:
                graph[prerequisite].append(dependent)

    visited = set()
    recursion_stack = set()
    cycles = []

    def dfs(course, path):
        visited.add(course)
        recursion_stack.add(course)
        path.append(course)

        for neighbor in graph[course]:

            if neighbor not in visited:
                dfs(neighbor, path)

            elif neighbor in recursion_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]

                if cycle not in cycles:
                    cycles.append(cycle)

        path.pop()
        recursion_stack.remove(course)

    for course in graph:
        if course not in visited:
            dfs(course, [])

    return cycles


def main():
    courses_data = load_json("courses.json")
    prerequisites_data = load_json("prerequisites.json")

    catalog = build_course_catalog(courses_data)
    prerequisites = prerequisites_data.get("prerequisites", {})

    errors, relationships = validate_prerequisites(
        catalog,
        prerequisites
    )

    cycles = detect_cycles(catalog, prerequisites)

    print("\n=== Prerequisite Integrity Validation ===\n")

    print(f"Courses in catalog: {len(catalog)}")
    print(f"Relationships found: {len(relationships)}")
    print(f"Basic integrity errors: {len(errors)}")
    print(f"Cycles detected: {len(cycles)}")

    if errors:
        print("\n=== Integrity Errors ===")
        for error in errors:
            print(f"[ERROR] {error}")

    if cycles:
        print("\n=== Circular Dependencies ===")
        for cycle in cycles:
            print("[CYCLE] " + " -> ".join(cycle))

    if errors or cycles:
        print("\nValidation FAILED.")
    else:
        print("\nValidation PASSED.")


if __name__ == "__main__":
    main()
