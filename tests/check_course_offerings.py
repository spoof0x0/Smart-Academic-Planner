
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    courses_data = load_json("courses.json")
    offerings_data = load_json("offerings.json")
    academic_rules = load_json("academic_rules.json")

    errors = []
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1

        if not condition:
            errors.append(message)

    # Build course catalog
    sections = [
        "fixed_courses",
        "university_electives",
        "specialized_electives_list_1",
        "specialized_electives_list_2",
    ]

    catalog = {}

    for section in sections:
        for course in courses_data.get(section, []):
            catalog[course["code"]] = course

    policies = offerings_data.get("offering_policy", {})

    # 1. Schema
    check(
        offerings_data.get("schema_version") == "1.0",
        "Invalid offerings schema_version"
    )

    check(
        set(policies.keys()) == {"Fall", "Spring", "Summer"},
        "Offering policies must define Fall, Spring, and Summer"
    )

    # 2. Fall policy
    fall = policies.get("Fall", {})

    check(
        fall.get("rule") == "odd_semesters",
        "Fall rule must be odd_semesters"
    )

    fall_included = fall.get("included_courses", [])

    check(
        isinstance(fall_included, list),
        "Fall included_courses must be a list"
    )

    if isinstance(fall_included, list):
        for code in fall_included:
            check(
                code in catalog,
                f"Fall includes unknown course: {code}"
            )

    # 3. Spring policy
    spring = policies.get("Spring", {})

    check(
        spring.get("rule") == "even_semesters",
        "Spring rule must be even_semesters"
    )

    spring_included = spring.get("included_courses", [])

    check(
        isinstance(spring_included, list),
        "Spring included_courses must be a list"
    )

    if isinstance(spring_included, list):
        for code in spring_included:
            check(
                code in catalog,
                f"Spring includes unknown course: {code}"
            )

    # 4. Summer policy
    summer = policies.get("Summer", {})

    check(
        summer.get("rule") == "all_courses",
        "Summer rule must be all_courses"
    )

    excluded_categories = summer.get("excluded_categories", [])

    check(
        isinstance(excluded_categories, list),
        "Summer excluded_categories must be a list"
    )

    # 5. Mandatory summer categories
    mandatory_categories = academic_rules.get(
        "summer_semester", {}
    ).get("mandatory_summer_categories", [])

    check(
        isinstance(mandatory_categories, list)
        and len(mandatory_categories) > 0,
        "Mandatory summer categories must be defined"
    )

    # Collect available categories
    course_categories = {
        course.get("category")
        for course in catalog.values()
        if course.get("category") is not None
    }

    if isinstance(excluded_categories, list):
        for category in excluded_categories:
            check(
                category in course_categories,
                f"Unknown excluded summer category: {category}"
            )

    # Check mandatory categories exist
    for category in mandatory_categories:
        check(
            category in course_categories,
            f"Mandatory summer category does not exist: {category}"
        )

        check(
            category not in excluded_categories,
            f"Mandatory summer category is excluded: {category}"
        )

    # 6. Validate course semester placement
    semester_courses = 0
    courses_without_semester = 0
    summer_only_courses = 0

    for code, course in catalog.items():
        category = course.get("category")
        semester = course.get("semester")

        if semester is None:
            courses_without_semester += 1
        else:
            check(
                isinstance(semester, int)
                and not isinstance(semester, bool)
                and 1 <= semester <= 10,
                f"{code}: invalid semester value"
            )

            if isinstance(semester, int) and not isinstance(semester, bool):
                semester_courses += 1

        # Summer-only category must not be included in Fall or Spring
        if category in mandatory_categories:
            summer_only_courses += 1

            check(
                code not in fall_included,
                f"{code}: summer-only course included in Fall"
            )

            check(
                code not in spring_included,
                f"{code}: summer-only course included in Spring"
            )

        # Other courses with a known semester follow parity rules
        elif isinstance(semester, int) and not isinstance(semester, bool):
            if semester % 2 == 1:
                check(
                    code not in spring_included,
                    f"{code}: odd-semester course included in Spring"
                )

            else:
                check(
                    code not in fall_included,
                    f"{code}: even-semester course included in Fall"
                )

    # 7. Duplicate exceptions
    for term, included in [
        ("Fall", fall_included),
        ("Spring", spring_included),
    ]:
        if isinstance(included, list):
            check(
                len(included) == len(set(included)),
                f"Duplicate course entries in {term} included_courses"
            )

    # Results
    print("\n=== Course Offering Validation ===\n")

    print(f"Courses in catalog: {len(catalog)}")
    print(f"Courses with semester: {semester_courses}")
    print(f"Courses without semester: {courses_without_semester}")
    print(f"Summer-only courses: {summer_only_courses}")
    print(f"Checks performed: {checks}")
    print(f"Errors found: {len(errors)}")

    if errors:
        print("\n=== Validation Errors ===")

        for error in errors:
            print(f"[ERROR] {error}")

        print("\nValidation FAILED.")

    else:
        print("\nValidation PASSED.")
        print("Course offering policies are consistent.")


if __name__ == "__main__":
    main()
