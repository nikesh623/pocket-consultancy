
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
            user = form.save()
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            messages.success(
                request,
                "Your student account has been created successfully.",
            )
            return redirect("core:dashboard")
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})
