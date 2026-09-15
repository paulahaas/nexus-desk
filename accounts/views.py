from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User

DEMO_ACCOUNTS = {
    "admin": "admin",
    "agent": "agente.n1.ana",
    "user": "ana.silva",
}


@login_required
def home(request):
    """Placeholder pós-login. Vira a fila de chamados na etapa "fila e detalhe"."""
    return render(request, "accounts/home.html")


def demo_login(request, role):
    """Login em 1 clique com uma conta fixa do seed_demo (ver DEMO_MODE)."""
    if not settings.DEMO_MODE or role not in DEMO_ACCOUNTS:
        raise Http404
    if request.method != "POST":
        raise Http404

    user = get_object_or_404(User, username=DEMO_ACCOUNTS[role])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("home")
