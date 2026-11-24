
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    courses_data = load_json("courses.json")

    slots = courses_data.get("elective_slots", [])

    elective_sections = {
        "university_elective": courses_data.get(
            "university_electives", []
        ),
        "specialized_elective_list_1": courses_data.get(
            "specialized_electives_list_1", []
        ),
        "specialized_elective_list_2": courses_data.get(
            "specialized_electives_list_2", []
        ),
    }

    errors = []
    slot_ids = []
    category_counts = Counter()

    print("\n=== Elective Slots Validation ===\n")

    # Build elective course catalog
    elective_catalog = {}

    for category, courses in elective_sections.items():
        for course in courses:
            elective_catalog[course["code"]] = course

    # Validate each slot
    for index, slot in enumerate(slots, start=1):

        slot_id = slot.get("id", f"Slot #{index}")
        category = slot.get("category")
        required_credits = slot.get("credit_hours")

        slot_ids.append(slot_id)

        print(f"Checking {slot_id}...")

        # Check required fields
        if not category:
            errors.append(f"{slot_id}: missing category")
            continue

        if category not in elective_sections:
            errors.append(
                f"{slot_id}: unknown category '{category}'"
            )
            continue

        category_counts[category] += 1

        if not isinstance(required_credits, (int, float)) or required_credits <= 0:
            errors.append(
                f"{slot_id}: invalid credit_hours"
            )
            continue

        # Check that the category has eligible courses
        eligible_courses = elective_sections[category]

        if not eligible_courses:
            errors.append(
                f"{slot_id}: no courses available in {category}"
            )
            continue

        # Check that at least one course matches slot credits
        matching_courses = [
            course
            for course in eligible_courses
            if course.get("credit_hours") == required_credits
        ]

        if not matching_courses:
            errors.append(
                f"{slot_id}: no eligible course matches "
                f"{required_credits} credit hours"
            )

    # Check duplicate slot IDs
    slot_id_counts = Counter(slot_ids)

    for slot_id, count in slot_id_counts.items():
        if count > 1:
            errors.append(f"Duplicate slot ID: {slot_id}")

    # Check duplicate elective course codes
    course_codes = [
        course["code"]
        for courses in elective_sections.values()
        for course in courses
    ]

    code_counts = Counter(course_codes)

    for code, count in code_counts.items():
        if count > 1:
            errors.append(
                f"Duplicate elective course code: {code}"
            )

    # Results
    print("\n=== Summary ===\n")

    print(f"Elective slots found: {len(slots)}")
    print(f"University elective slots: "
          f"{category_counts['university_elective']}")
    print(f"Specialized List 1 slots: "
          f"{category_counts['specialized_elective_list_1']}")
    print(f"Specialized List 2 slots: "
          f"{category_counts['specialized_elective_list_2']}")
    print(f"Elective courses found: {len(elective_catalog)}")
    print(f"Errors found: {len(errors)}")

    if errors:
        print("\n=== Errors ===")
        for error in errors:
            print(f"[ERROR] {error}")

        print("\nValidation FAILED.")
    else:
        print("\nValidation PASSED.")


if __name__ == "__main__":
    main()
