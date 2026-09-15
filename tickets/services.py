"""Regras de negócio do ciclo de vida do chamado.

Toda transição de status passa por `transition_status`, a única fonte
de verdade sobre quais mudanças são válidas. Qualquer outra mudança de
campo relevante (prioridade, responsável, categoria, nível de suporte)
passa por `change_field`, que gera o mesmo tipo de evento de timeline.
"""

from django.utils import timezone

from tickets.models import Status, Ticket, TicketEvent


class InvalidTransitionError(Exception):
    pass


VALID_TRANSITIONS: dict[str, set[str]] = {
    Status.ABERTO: {Status.EM_ANDAMENTO, Status.RESOLVIDO},
    Status.EM_ANDAMENTO: {Status.AGUARDANDO_RESPOSTA, Status.RESOLVIDO, Status.ABERTO},
    Status.AGUARDANDO_RESPOSTA: {Status.EM_ANDAMENTO, Status.RESOLVIDO},
    Status.RESOLVIDO: {Status.FECHADO, Status.REABERTO},
    Status.FECHADO: set(),
    Status.REABERTO: {Status.EM_ANDAMENTO},
}


def transition_status(ticket: Ticket, new_status: str, *, author=None) -> Ticket:
    """Move o chamado pra `new_status`, validando a transição e registrando o evento."""
    old_status = ticket.status
    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Não é possível ir de {old_status} para {new_status}."
        )

    now = timezone.now()
    ticket.status = new_status

    if old_status == Status.ABERTO and ticket.first_response_at is None:
        ticket.first_response_at = now

    if new_status == Status.RESOLVIDO:
        ticket.resolved_at = now
    elif new_status == Status.FECHADO:
        ticket.closed_at = now
    elif new_status == Status.REABERTO:
        ticket.resolved_at = None

    ticket.save()
    TicketEvent.objects.create(
        ticket=ticket,
        author=author,
        field="status",
        from_value=old_status,
        to_value=new_status,
    )
    return ticket


def change_field(ticket: Ticket, field_name: str, new_value, *, author=None) -> Ticket:
    """Muda um campo do chamado (prioridade, responsável, categoria...) e registra o evento."""
    old_value = getattr(ticket, field_name)
    if old_value == new_value:
        return ticket

    setattr(ticket, field_name, new_value)
    ticket.save(update_fields=[field_name])
    TicketEvent.objects.create(
        ticket=ticket,
        author=author,
        field=field_name,
        from_value="" if old_value is None else str(old_value),
        to_value="" if new_value is None else str(new_value),
    )
    return ticket
