from django import template

from tickets.models import Priority, Status
from tickets.sla import SLAState

register = template.Library()

_STATUS_COLOR = {
    Status.ABERTO: "info",
    Status.EM_ANDAMENTO: "accent",
    Status.AGUARDANDO_RESPOSTA: "warn",
    Status.RESOLVIDO: "ok",
    Status.FECHADO: "neutral",
    Status.REABERTO: "danger",
}

_PRIORITY_COLOR = {
    Priority.BAIXA: "neutral",
    Priority.MEDIA: "info",
    Priority.ALTA: "warn",
    Priority.CRITICA: "danger",
}

_SLA_COLOR = {
    SLAState.GREEN: "ok",
    SLAState.YELLOW: "warn",
    SLAState.RED: "danger",
}

_BADGE_CLASSES = {
    "ok": "bg-sla-ok-dim text-sla-ok",
    "warn": "bg-sla-warn-dim text-sla-warn",
    "danger": "bg-sla-danger-dim text-sla-danger",
    "info": "bg-sla-info-dim text-sla-info",
    "accent": "bg-accent-dim text-accent",
    "neutral": "bg-surface-2 text-text-faint",
}

_DOT_CLASSES = {
    "ok": "bg-sla-ok",
    "warn": "bg-sla-warn",
    "danger": "bg-sla-danger",
    "info": "bg-sla-info",
    "accent": "bg-accent",
    "neutral": "bg-text-faint",
}


@register.filter
def status_badge(status):
    return _BADGE_CLASSES[_STATUS_COLOR.get(status, "neutral")]


@register.filter
def priority_badge(priority):
    return _BADGE_CLASSES[_PRIORITY_COLOR.get(priority, "neutral")]


@register.filter
def sla_badge(state):
    return _BADGE_CLASSES[_SLA_COLOR.get(state, "neutral")]


@register.filter
def sla_dot(state):
    return _DOT_CLASSES[_SLA_COLOR.get(state, "neutral")]


@register.filter
def display_name(user):
    """Nome de exibição de um User, sem quebrar quando `user` é None
    (ex.: chamado sem responsável) — encadear |default: em cima de
    ticket.assignee.username faz o Django tentar resolver o atributo
    em None antes de aplicar o default, e isso levanta exceção."""
    if user is None:
        return "—"
    return user.get_full_name() or user.username
