"""Controle de acesso por papel (RBAC).

Checagem de papel (Usuário/Agente/Admin) vira 403 — a pessoa está
autenticada, só não tem permissão pra ver aquilo. Checagem de dono de
recurso (ex.: chamado de outra pessoa) é responsabilidade de cada view
e deve virar 404, não 403, pra não revelar que o recurso existe.
"""

from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role not in self.allowed_roles:
            raise PermissionDenied("Seu papel não tem acesso a esta página.")
        return super().dispatch(request, *args, **kwargs)


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                raise PermissionDenied("Seu papel não tem acesso a esta página.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
