
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILES = {
    "courses": DATA_DIR / "courses.json",
    "prerequisites": DATA_DIR / "prerequisites.json",
    "academic_rules": DATA_DIR / "academic_rules.json",
    "offerings": DATA_DIR / "offerings.json"
}

errors = []
warnings = []


def error(message):
    errors.append(message)


def warning(message):
    warnings.append(message)


def load_json(name):
    path = FILES[name]

    if not path.exists():
        error(f"Missing file: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            error(f"{name}.json must contain a JSON object.")
            return None

        if data.get("schema_version") != "1.0":
            warning(f"{name}.json has an unexpected schema version.")

        return data

    except json.JSONDecodeError as exc:
        error(f"{name}.json has invalid JSON: {exc}")
    except OSError as exc:
        error(f"Cannot read {name}.json: {exc}")

    return None


def validate_courses(data):
    if data is None:
        return set(), {}

    required_sections = [
        "fixed_courses",
        "elective_slots",
        "university_electives",
        "specialized_electives_list_1",
        "specialized_electives_list_2"
    ]

    for section in required_sections:
        if not isinstance(data.get(section), list):
            error(f"courses.json: '{section}' must be a list.")
            data[section] = []

    courses = {}
    slots = set()

    course_sections = [
        "fixed_courses",
        "university_electives",
        "specialized_electives_list_1",
        "specialized_electives_list_2"
    ]

    for section in course_sections:
        print(f"{section}: {len(data[section])}")
        for index, course in enumerate(data[section]):

            if not isinstance(course, dict):
                error(f"{section}[{index}] must be an object.")
                continue

            code = course.get("code")

            if not isinstance(code, str) or not code.strip():
                error(f"{section}[{index}] has an invalid course code.")
                continue

            if code in courses:
                error(f"Duplicate course code: {code}")
                continue

            courses[code] = course

            credits = course.get("credit_hours")

            if not isinstance(credits, (int, float)) or isinstance(credits, bool) or credits <= 0:
                error(f"{code}: invalid credit_hours.")

            semester = course.get("semester")

            if semester is not None:
                if not isinstance(semester, int) or isinstance(semester, bool) or not 1 <= semester <= 10:
                    error(f"{code}: semester must be between 1 and 10.")

            if section == "specialized_electives_list_1":
                if course.get("category") != "specialized_elective_list_1":
                    error(f"{code}: incorrect category for List 1.")

                if course.get("elective_list") != 1:
                    error(f"{code}: elective_list must be 1.")

            elif section == "specialized_electives_list_2":
                if course.get("category") != "specialized_elective_list_2":
                    error(f"{code}: incorrect category for List 2.")

                if course.get("elective_list") != 2:
                    error(f"{code}: elective_list must be 2.")

                if "semester" in course:
                    error(f"{code}: List 2 courses must not have a semester field.")

            elif section == "university_electives":
                if course.get("category") != "university_elective":
                    error(f"{code}: incorrect university elective category.")

    for index, slot in enumerate(data["elective_slots"]):

        if not isinstance(slot, dict):
            error(f"elective_slots[{index}] must be an object.")
            continue

        slot_id = slot.get("slot_id")

        if not isinstance(slot_id, str) or not slot_id:
            error(f"elective_slots[{index}] has an invalid slot_id.")
            continue

        if slot_id in slots:
            error(f"Duplicate elective slot: {slot_id}")

        slots.add(slot_id)

        category = slot.get("category")

        allowed_categories = {
            "university_elective",
            "specialized_elective_list_1",
            "specialized_elective_list_2"
        }

        if category not in allowed_categories:
            error(f"{slot_id}: invalid elective category.")

        if not isinstance(slot.get("credit_hours"), (int, float)):
            error(f"{slot_id}: invalid credit_hours.")

    print(f"Courses found: {len(courses)}")
    print(f"Elective slots found: {len(slots)}")

    return set(courses), courses


def validate_prerequisites(data, course_codes):

    if data is None:
        return

    prerequisites = data.get("prerequisites")

    if not isinstance(prerequisites, dict):
        error("prerequisites.json must contain a prerequisites object.")
        return

    graph = defaultdict(list)

    for source, dependents in prerequisites.items():

        if source not in course_codes:
            error(f"Unknown prerequisite course: {source}")

        if not isinstance(dependents, list):
            error(f"{source}: dependent courses must be a list.")
            continue

        if len(dependents) != len(set(dependents)):
            error(f"{source}: duplicate dependent course.")

        for dependent in dependents:

            if dependent not in course_codes:
                error(f"{source} -> {dependent}: unknown course.")
                continue

            if source == dependent:
                error(f"{source}: course cannot depend on itself.")
                continue

            graph[source].append(dependent)

    # Detect circular prerequisite dependencies
    visited = set()
    active = set()

    def dfs(node):
        if node in active:
            return True

        if node in visited:
            return False

        visited.add(node)
        active.add(node)

        for neighbor in graph[node]:
            if dfs(neighbor):
                return True

        active.remove(node)
        return False

    for course in course_codes:
        if dfs(course):
            error("Circular prerequisite dependency detected.")
            break

    print(f"Prerequisite relationships: {sum(len(v) for v in graph.values())}")


def validate_academic_rules(data):

    if data is None:
        return

    limits = data.get("credit_hour_limits", {})
    rules = limits.get("rules", [])

    if not isinstance(rules, list) or not rules:
        error("academic_rules.json: credit hour rules are missing.")
    else:
        previous_max = None
        previous_max_inclusive = False

        for rule in rules:

            minimum = rule.get("min_gpa")
            maximum = rule.get("max_gpa")
            max_hours = rule.get("max_credit_hours")

            if not isinstance(minimum, (int, float)):
                error("Invalid min_gpa in credit hour rules.")
                continue

            if not isinstance(max_hours, int) or max_hours <= 0:
                error("Invalid max_credit_hours.")
                
            if maximum is not None and maximum <= minimum:
                error("Invalid GPA range.")

            if previous_max is not None:
                if minimum != previous_max:
                    error("Gap or overlap detected in GPA ranges.")

                if previous_max_inclusive and rule.get("min_inclusive", False):
                    error("Overlapping GPA range boundaries.")

            previous_max = maximum
            previous_max_inclusive = rule.get("max_inclusive", False)

    summer = data.get("summer_semester", {})

    if not isinstance(summer.get("max_credit_hours"), int) or summer.get("max_credit_hours", 0) <= 0:
        error("Invalid summer maximum credit hours.")

    gpa = data.get("gpa_calculation", {})

    if gpa.get("repeated_course_policy") not in [
        "grade_replacement",
        "grade_replacement_if_higher"
    ]:
        error("Unknown repeated course policy.")

    warnings_data = data.get("academic_warnings", {})

    if warnings_data.get("dismissal_after_warnings") != 6:
        warning("Academic dismissal threshold differs from 6 warnings.")

    graduation = data.get("graduation_requirements", {})

    if graduation.get("minimum_final_cumulative_gpa") != 2.0:
        warning("Graduation GPA requirement differs from 2.0.")

    print("Academic rules checked.")


def validate_offerings(data, courses, course_data, academic_rules):

    if data is None:
        return

    policies = data.get("offering_policy")

    if not isinstance(policies, dict):
        error("offerings.json: offering_policy is missing.")
        return

    expected_rules = {
        "Fall": "odd_semesters",
        "Spring": "even_semesters",
        "Summer": "all_courses"
    }

    for semester, expected_rule in expected_rules.items():

        policy = policies.get(semester)

        if not isinstance(policy, dict):
            error(f"Missing offering policy for {semester}.")
            continue

        if policy.get("rule") != expected_rule:
            error(f"{semester}: expected rule '{expected_rule}'.")

        included = policy.get("included_courses", [])

        if semester == "Summer":
            excluded = policy.get("excluded_categories", [])

            if not isinstance(excluded, list):
                error("Summer excluded_categories must be a list.")
                excluded = []

        else:
            if not isinstance(included, list):
                error(f"{semester}: included_courses must be a list.")
                continue

        if not isinstance(included, list):
            error(f"{semester}: included_courses must be a list.")
            continue

        if len(included) != len(set(included)):
            error(f"{semester}: duplicate included course.")

        for code in included:
            if code not in courses:
                error(f"{semester}: unknown included course {code}.")

    # Check that all courses with a semester are assigned
    # to the correct Fall or Spring parity.
    fall = policies.get("Fall", {})
    spring = policies.get("Spring", {})

    fall_extras = set(fall.get("included_courses", []))
    spring_extras = set(spring.get("included_courses", []))

    if fall_extras & spring_extras:
        error("A course cannot be an extra inclusion in both Fall and Spring.")

    for code, course in course_data.items():

        semester = course.get("semester")

        if semester is None:
            continue

        if not isinstance(semester, int):
            continue

        if semester % 2 == 1:
            if code in spring_extras:
                error(f"{code}: odd-semester course cannot be a Spring exception.")

        else:
            if code in fall_extras:
                error(f"{code}: even-semester course cannot be a Fall exception.")

    # Check Summer mandatory categories
    if academic_rules is not None:
        mandatory = academic_rules.get(
            "summer_semester", {}
        ).get("mandatory_summer_categories", [])

        excluded = policies.get("Summer", {}).get(
            "excluded_categories", []
        )

        if set(mandatory) & set(excluded):
            error("A mandatory Summer category is excluded from Summer offerings.")

    print("Offering policies checked.")


def main():

    print("\n=== Academic Data Validator ===\n")

    courses_data = load_json("courses")
    prerequisites_data = load_json("prerequisites")
    rules_data = load_json("academic_rules")
    offerings_data = load_json("offerings")

    course_codes, course_data = validate_courses(courses_data)

    validate_prerequisites(
        prerequisites_data,
        course_codes
    )

    validate_academic_rules(rules_data)

    validate_offerings(
        offerings_data,
        course_codes,
        course_data,
        rules_data
    )

    print("\n=== Validation Results ===")

    if warnings:
        print(f"\nWarnings: {len(warnings)}")
        for item in warnings:
            print(f"[WARNING] {item}")

    if errors:
        print(f"\nErrors: {len(errors)}")
        for item in errors:
            print(f"[ERROR] {item}")

        print("\nValidation FAILED.")
        raise SystemExit(1)

    print("\nValidation PASSED.")
    print("All checked data files are structurally consistent.")


if __name__ == "__main__":
    main()
