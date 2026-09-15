"""Relógio de SLA: só conta minutos dentro do horário comercial, pula
feriados e fins de semana, e pausa enquanto o chamado está
AGUARDANDO_RESPOSTA (o tempo pausado empurra o prazo pra frente).

Isolado aqui, sem nada de views/HTTP, pra poder testar cada regra
(horário comercial, feriado, fim de semana, pausa, limiares de 75% e
vencimento) isoladamente.
"""

import datetime
from dataclasses import dataclass

from django.utils import timezone

from tickets.models import BusinessHours, Holiday, SLAPolicy, Status, Ticket

YELLOW_THRESHOLD_PERCENT = 75


class SLAState:
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass
class SLAStatus:
    target_minutes: int
    elapsed_minutes: float
    percent_consumed: float
    deadline: datetime.datetime
    state: str
    is_paused: bool


def _business_hours_map() -> dict[int, tuple[datetime.time, datetime.time]]:
    return {bh.weekday: (bh.start_time, bh.end_time) for bh in BusinessHours.objects.all()}


def _holiday_set() -> set[datetime.date]:
    return set(Holiday.objects.values_list("date", flat=True))


def business_minutes_between(
    start: datetime.datetime,
    end: datetime.datetime,
    hours_map: dict | None = None,
    holidays: set | None = None,
) -> float:
    """Minutos úteis entre duas datas (aware), considerando horário comercial e feriados."""
    if start is None or end is None or start >= end:
        return 0.0
    if hours_map is None:
        hours_map = _business_hours_map()
    if holidays is None:
        holidays = _holiday_set()

    tz = timezone.get_current_timezone()
    local_start = timezone.localtime(start, tz)
    local_end = timezone.localtime(end, tz)

    total = datetime.timedelta()
    current_date = local_start.date()
    while current_date <= local_end.date():
        hours = hours_map.get(current_date.weekday())
        if hours and current_date not in holidays:
            day_start = timezone.make_aware(
                datetime.datetime.combine(current_date, hours[0]), tz
            )
            day_end = timezone.make_aware(
                datetime.datetime.combine(current_date, hours[1]), tz
            )
            window_start = max(day_start, start)
            window_end = min(day_end, end)
            if window_start < window_end:
                total += window_end - window_start
        current_date += datetime.timedelta(days=1)

    return total.total_seconds() / 60


def add_business_minutes(
    start: datetime.datetime,
    minutes: float,
    hours_map: dict | None = None,
    holidays: set | None = None,
) -> datetime.datetime:
    """Retorna o instante `minutes` minutos úteis à frente de `start`."""
    if hours_map is None:
        hours_map = _business_hours_map()
    if holidays is None:
        holidays = _holiday_set()

    tz = timezone.get_current_timezone()
    remaining = datetime.timedelta(minutes=minutes)
    current = timezone.localtime(start, tz)
    current_date = current.date()

    for _ in range(3650):  # limite de segurança: ~10 anos de dias corridos
        hours = hours_map.get(current_date.weekday())
        if hours and current_date not in holidays:
            day_start = timezone.make_aware(
                datetime.datetime.combine(current_date, hours[0]), tz
            )
            day_end = timezone.make_aware(
                datetime.datetime.combine(current_date, hours[1]), tz
            )
            window_start = max(day_start, current)
            if window_start < day_end:
                available = day_end - window_start
                if available >= remaining:
                    return window_start + remaining
                remaining -= available
        current_date += datetime.timedelta(days=1)
        current = timezone.make_aware(
            datetime.datetime.combine(current_date, datetime.time.min), tz
        )

    return current


def _status_intervals(ticket: Ticket, until: datetime.datetime):
    """[(status, começo, fim), ...] cobrindo created_at até `until`."""
    events = list(
        ticket.events.filter(field="status", created_at__lte=until).order_by("created_at")
    )
    timeline = [(ticket.created_at, Status.ABERTO)]
    for event in events:
        timeline.append((event.created_at, event.to_value))

    intervals = []
    for i, (start, status) in enumerate(timeline):
        end = timeline[i + 1][0] if i + 1 < len(timeline) else until
        end = min(end, until)
        if start < end:
            intervals.append((status, start, end))
    return intervals


def _paused_business_minutes(
    ticket: Ticket, until: datetime.datetime, hours_map: dict, holidays: set
) -> float:
    total = 0.0
    for status, start, end in _status_intervals(ticket, until):
        if status == Status.AGUARDANDO_RESPOSTA:
            total += business_minutes_between(start, end, hours_map, holidays)
    return total


def _evaluate(ticket: Ticket, target_minutes: int, until: datetime.datetime) -> SLAStatus:
    hours_map = _business_hours_map()
    holidays = _holiday_set()

    paused_minutes = _paused_business_minutes(ticket, until, hours_map, holidays)
    elapsed_minutes = (
        business_minutes_between(ticket.created_at, until, hours_map, holidays) - paused_minutes
    )
    deadline = add_business_minutes(
        ticket.created_at, target_minutes + paused_minutes, hours_map, holidays
    )
    percent_consumed = (elapsed_minutes / target_minutes * 100) if target_minutes else 0.0

    if until >= deadline:
        state = SLAState.RED
    elif percent_consumed >= YELLOW_THRESHOLD_PERCENT:
        state = SLAState.YELLOW
    else:
        state = SLAState.GREEN

    return SLAStatus(
        target_minutes=target_minutes,
        elapsed_minutes=elapsed_minutes,
        percent_consumed=percent_consumed,
        deadline=deadline,
        state=state,
        is_paused=ticket.status == Status.AGUARDANDO_RESPOSTA,
    )


def first_response_sla(ticket: Ticket, sla_policy: SLAPolicy | None = None) -> SLAStatus:
    policy = sla_policy or SLAPolicy.objects.get(priority=ticket.priority)
    until = ticket.first_response_at or timezone.now()
    return _evaluate(ticket, policy.first_response_minutes, until)


def resolution_sla(ticket: Ticket, sla_policy: SLAPolicy | None = None) -> SLAStatus:
    policy = sla_policy or SLAPolicy.objects.get(priority=ticket.priority)
    until = ticket.resolved_at or timezone.now()
    return _evaluate(ticket, policy.resolution_minutes, until)
