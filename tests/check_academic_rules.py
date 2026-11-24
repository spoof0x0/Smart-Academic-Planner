
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_FILE = BASE_DIR / "data" / "academic_rules.json"


def load_json():
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    data = load_json()
    errors = []
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1

        if not condition:
            errors.append(message)

    # 1. Schema version
    check(
        data.get("schema_version") == "1.0",
        "Invalid or missing schema_version"
    )

    # 2. Credit hour limits
    credit_data = data.get("credit_hour_limits", {})

    check(
        credit_data.get("type") == "cumulative_gpa_based",
        "Invalid credit_hour_limits type"
    )

    rules = credit_data.get("rules", [])

    check(
        isinstance(rules, list) and len(rules) == 3,
        "Expected exactly 3 GPA credit-hour rules"
    )

    expected_rules = [
        (0.0, 2.0, True, False, 14),
        (2.0, 3.0, True, False, 18),
        (3.0, 4.0, True, True, 21),
    ]

    if isinstance(rules, list) and len(rules) == 3:

        for index, (rule, expected) in enumerate(
            zip(rules, expected_rules), start=1
        ):
            min_gpa, max_gpa, min_inc, max_inc, credits = expected

            check(
                rule.get("min_gpa") == min_gpa,
                f"Rule {index}: incorrect min_gpa"
            )

            check(
                rule.get("max_gpa") == max_gpa,
                f"Rule {index}: incorrect max_gpa"
            )

            check(
                rule.get("min_inclusive") is min_inc,
                f"Rule {index}: incorrect min_inclusive"
            )

            check(
                rule.get("max_inclusive") is max_inc,
                f"Rule {index}: incorrect max_inclusive"
            )

            check(
                rule.get("max_credit_hours") == credits,
                f"Rule {index}: incorrect max_credit_hours"
            )

            check(
                rule.get("min_gpa", -1) < rule.get("max_gpa", -1),
                f"Rule {index}: invalid GPA range"
            )

            check(
                isinstance(rule.get("max_credit_hours"), int)
                and rule["max_credit_hours"] > 0,
                f"Rule {index}: invalid credit-hour limit"
            )

        # Check continuity and boundary inclusivity
        for index in range(len(rules) - 1):
            current = rules[index]
            following = rules[index + 1]

            check(
                current.get("max_gpa") == following.get("min_gpa"),
                f"Gap or overlap between rules {index + 1} "
                f"and {index + 2}"
            )

            check(
                current.get("max_inclusive") is False
                and following.get("min_inclusive") is True,
                f"Invalid shared GPA boundary between rules "
                f"{index + 1} and {index + 2}"
            )

        check(
            rules[0].get("min_gpa") == 0.0
            and rules[0].get("min_inclusive") is True,
            "GPA ranges must start inclusively at 0.0"
        )

        check(
            rules[-1].get("max_gpa") == 4.0
            and rules[-1].get("max_inclusive") is True,
            "GPA ranges must end inclusively at 4.0"
        )

    # 3. Summer semester
    summer = data.get("summer_semester", {})

    check(
        summer.get("max_credit_hours") == 6,
        "Summer maximum credit hours must be 6"
    )

    check(
        summer.get("course_availability")
        == "depends_on_official_offerings",
        "Invalid summer course availability policy"
    )

    check(
        summer.get("mandatory_summer_categories") == ["summer"],
        "Invalid mandatory summer categories"
    )

    # 4. GPA calculation
    gpa = data.get("gpa_calculation", {})

    check(
        gpa.get("repeated_course_policy")
        == "grade_replacement_if_higher",
        "Invalid repeated course policy"
    )

    check(
        gpa.get("grading_scale") is None,
        "Grading scale should remain unconfirmed (null)"
    )

    check(
        gpa.get("grade_points_mapping") is None,
        "Grade points mapping should remain unconfirmed (null)"
    )

    # 5. Academic warnings
    warnings = data.get("academic_warnings", {})

    check(
        warnings.get("condition")
        == "cumulative_gpa_below_2.0_at_semester_end",
        "Invalid academic warning condition"
    )

    check(
        warnings.get("warning_counting")
        == "cumulative_not_necessarily_consecutive",
        "Invalid warning counting policy"
    )

    check(
        warnings.get("dismissal_after_warnings") == 6,
        "Dismissal threshold must be 6 warnings"
    )

    # 6. Graduation requirements
    graduation = data.get("graduation_requirements", {})

    check(
        graduation.get("minimum_final_cumulative_gpa") == 2.0,
        "Minimum graduation GPA must be 2.0"
    )

    check(
        graduation.get("graduation_with_gpa_below_minimum_allowed")
        is False,
        "Graduation below minimum GPA must not be allowed"
    )

    # 7. Unconfirmed policies
    unconfirmed = data.get("unconfirmed_policies")

    check(
        isinstance(unconfirmed, list) and len(unconfirmed) > 0,
        "Unconfirmed policies must be a non-empty list"
    )

    if isinstance(unconfirmed, list):
        check(
            all(isinstance(item, str) and item.strip()
                for item in unconfirmed),
            "Unconfirmed policies must contain non-empty strings"
        )

    # Results
    print("\n=== Academic Rules Validation ===\n")
    print(f"Checks performed: {checks}")
    print(f"Errors found: {len(errors)}")

    if errors:
        print("\n=== Validation Errors ===")

        for error in errors:
            print(f"[ERROR] {error}")

        print("\nValidation FAILED.")

    else:
        print("\nValidation PASSED.")
        print("All confirmed academic rules are consistent.")

    print(
        f"\nUnconfirmed policies: "
        f"{len(unconfirmed) if isinstance(unconfirmed, list) else 0}"
    )


if __name__ == "__main__":
    main()
