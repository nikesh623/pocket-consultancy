
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import StudentRegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # Public registrations must always be students.
            user.role = user.Role.STUDENT

            # Require administrator approval before login.
            user.approval_status = user.ApprovalStatus.PENDING
            user.is_active = False

            user.save()

            messages.success(
                request,
                "Registration submitted successfully. "
                "Your account is pending administrator approval. "
                "You will be able to log in after approval.",
            )
            return redirect("accounts:login")
    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )
