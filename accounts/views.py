from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """Placeholder pós-login. Vira a fila de chamados na etapa "fila e detalhe"."""
    return render(request, "accounts/home.html")
