
import json
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

COURSES_FILE = DATA_DIR / "courses.json"
PREREQUISITES_FILE = DATA_DIR / "prerequisites.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_course_catalog(courses_data):
    catalog = {}

    sections = [
        "fixed_courses",
        "university_electives",
        "specialized_electives_list_1",
        "specialized_electives_list_2",
    ]

    for section in sections:
        for course in courses_data.get(section, []):
            catalog[course["code"]] = course

    return catalog


def validate_prerequisite_order(catalog, prerequisites_data):
    relationships = prerequisites_data.get("prerequisites", {})

    checked = 0
    skipped = 0
    errors = []

    for prerequisite_code, dependent_courses in relationships.items():

        prerequisite = catalog.get(prerequisite_code)

        if prerequisite is None:
            continue

        prerequisite_semester = prerequisite.get("semester")

        for dependent_code in dependent_courses:

            dependent = catalog.get(dependent_code)

            if dependent is None:
                continue

            dependent_semester = dependent.get("semester")

            # Cannot compare courses without semester information
            if prerequisite_semester is None or dependent_semester is None:
                skipped += 1
                continue

            checked += 1

            # A prerequisite must be completed before its dependent course
            if prerequisite_semester >= dependent_semester:
                errors.append({
                    "prerequisite": prerequisite_code,
                    "prerequisite_semester": prerequisite_semester,
                    "dependent": dependent_code,
                    "dependent_semester": dependent_semester,
                })

    print("\n=== Prerequisite Semester Order Validation ===\n")
    print(f"Relationships checked: {checked}")
    print(f"Relationships skipped: {skipped}")
    print(f"Violations found: {len(errors)}")

    if errors:
        print("\n=== Violations ===")

        for error in errors:
            print(
                f"[ERROR] {error['prerequisite']} "
                f"(Semester {error['prerequisite_semester']}) "
                f"-> {error['dependent']} "
                f"(Semester {error['dependent_semester']})"
            )

        print("\nValidation FAILED.")
        return False

    print("\nValidation PASSED.")
    return True


def main():
    courses_data = load_json(COURSES_FILE)
    prerequisites_data = load_json(PREREQUISITES_FILE)

    catalog = build_course_catalog(courses_data)

    validate_prerequisite_order(catalog, prerequisites_data)


if __name__ == "__main__":
    main()
