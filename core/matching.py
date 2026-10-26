
from decimal import Decimal

from .models import Course


def match_courses(profile):
    """
    Return active courses with transparent matching assessments.

    This is a guidance tool, not an admission decision.
    Budget comparisons are made only when currencies match.
    """
    courses = (
        Course.objects.filter(
            is_active=True,
            university__is_active=True,
            university__country__is_active=True,
        )
        .select_related("university", "university__country")
        .order_by("name")
    )

    results = []

    for course in courses:
        reasons = []
        concerns = []
        unknowns = []

        # 1. Academic score
        if profile.academic_score is None:
            unknowns.append("Your academic score has not been provided.")
        elif course.minimum_academic_score is None:
            unknowns.append(
                "The course's minimum academic score is not specified."
            )
        elif profile.academic_score >= course.minimum_academic_score:
            reasons.append(
                "Your academic score meets the listed minimum."
            )
        else:
            concerns.append(
                "Your academic score is below the listed minimum."
            )

        # 2. Study level
        if not profile.preferred_study_level:
            unknowns.append("Your preferred study level is not selected.")
        elif profile.preferred_study_level == course.study_level:
            reasons.append("The study level matches your preference.")
        else:
            concerns.append("The study level differs from your preference.")

        # 3. Preferred country
        if profile.preferred_country_id is None:
            unknowns.append("You have not selected a preferred country.")
        elif profile.preferred_country_id == course.university.country_id: # type: ignore
            reasons.append("The country matches your preference.")
        else:
            concerns.append("The course is in a different country.")


        # 4. Annual tuition budget
        if profile.annual_budget is None:
            unknowns.append("Your annual budget has not been provided.")
        elif not profile.annual_budget_currency:
            unknowns.append("Your budget currency is not specified.")
        elif profile.annual_budget_currency != course.currency:
            unknowns.append(
                "Budget and tuition currencies differ; no conversion was applied."
            )
        elif profile.annual_budget >= course.annual_tuition_fee:
            reasons.append(
                "Annual tuition is within your stated budget."
            )
        else:
            concerns.append(
                "Annual tuition exceeds your stated budget."
            )

        # A transparent assessment, not a probability of admission.
        if concerns:
            status = "needs_review"
            label = "Needs review"
        elif unknowns:
            status = "insufficient_data"
            label = "Insufficient information"
        else:
            status = "matches"
            label = "Matches your stated criteria"

        results.append(
            {
                "course": course,
                "status": status,
                "label": label,
                "reasons": reasons,
                "concerns": concerns,
                "unknowns": unknowns,
            }
        )

    # Show the strongest complete matches first.
    results.sort(
        key=lambda item: (
            item["status"] != "matches",
            item["status"] != "insufficient_data",
            item["course"].name.lower(),
        )
    )

    return results
