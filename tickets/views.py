from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from accounts.permissions import role_required
from tickets import sla as sla_service
from tickets.models import Category, Priority, Status, SupportLevel, Ticket
from tickets.services import change_field

PAGE_SIZE = 25

SORT_OPTIONS = {
    "recentes": ("-created_at", "Mais recentes"),
    "antigos": ("created_at", "Mais antigos"),
    "prioridade": ("-priority", "Prioridade"),
    "id": ("-readable_id", "ID"),
}


def _base_queryset(user):
    qs = Ticket.objects.select_related("requester", "assignee", "category")
    if user.is_user_role:
        return qs.filter(requester=user)
    return qs


def _apply_filters(qs, params, user):
    status = params.get("status")
    if status in Status.values:
        qs = qs.filter(status=status)

    priority = params.get("priority")
    if priority in Priority.values:
        qs = qs.filter(priority=priority)

    category = params.get("category")
    if category and category.isdigit():
        qs = qs.filter(category_id=category)

    level = params.get("level")
    if level in SupportLevel.values:
        qs = qs.filter(support_level=level)

    assignee = params.get("assignee")
    if assignee and assignee.isdigit():
        qs = qs.filter(assignee_id=assignee)

    if params.get("mine") == "1":
        qs = qs.filter(assignee=user)

    if params.get("unassigned") == "1":
        qs = qs.filter(assignee__isnull=True)

    query = params.get("q", "").strip()
    if query:
        vector = SearchVector(
            "readable_id",
            "title",
            "description",
            "requester__first_name",
            "requester__last_name",
            "requester__username",
        )
        qs = qs.annotate(search=vector).filter(search=SearchQuery(query, config="portuguese"))

    return qs


def _filter_by_risk(qs, order_by):
    """"Em risco" (amarelo+vermelho) precisa da SLA calculada em Python, então
    filtra antes de paginar, só sobre os chamados ainda ativos."""
    hours_map = sla_service.business_hours_map()
    holidays = sla_service.holiday_set()
    policies = sla_service.sla_policy_map()

    candidates = qs.exclude(status__in=[Status.RESOLVIDO, Status.FECHADO])
    candidates = candidates.prefetch_related("events")

    at_risk_ids = []
    for ticket in candidates:
        policy = policies.get(ticket.priority)
        sla = sla_service.active_sla(ticket, policy, hours_map, holidays)
        if sla.state in (sla_service.SLAState.YELLOW, sla_service.SLAState.RED):
            at_risk_ids.append(ticket.pk)

    related = ("requester", "assignee", "category")
    return Ticket.objects.filter(pk__in=at_risk_ids).select_related(*related).order_by(order_by)


def _attach_sla(tickets):
    hours_map = sla_service.business_hours_map()
    holidays = sla_service.holiday_set()
    policies = sla_service.sla_policy_map()
    for ticket in tickets:
        policy = policies.get(ticket.priority)
        ticket.sla = sla_service.active_sla(ticket, policy, hours_map, holidays)
    return tickets


def _querystring_without(params, *excluded):
    kept = [(k, v) for k, v in params.items() if k not in excluded]
    return "&".join(f"{k}={v}" for k, v in kept)


@login_required
def queue(request):
    user = request.user
    params = request.GET

    sort_key = params.get("sort") if params.get("sort") in SORT_OPTIONS else "recentes"
    order_by, _ = SORT_OPTIONS[sort_key]

    qs = _apply_filters(_base_queryset(user), params, user).order_by(order_by)
    if params.get("risk") == "1":
        qs = _filter_by_risk(qs, order_by)

    qs = qs.prefetch_related("events")
    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(params.get("page"))
    _attach_sla(page_obj.object_list)

    context = {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "agents": User.objects.filter(role=User.Role.AGENT),
        "status_choices": Status.choices,
        "priority_choices": Priority.choices,
        "level_choices": SupportLevel.choices,
        "sort_display": {key: label for key, (_, label) in SORT_OPTIONS.items()},
        "current_sort": sort_key,
        "querystring": _querystring_without(params, "page"),
        "can_manage_queue": user.is_agent or user.is_admin_role,
    }

    template = "tickets/partials/queue_results.html" if request.htmx else "tickets/queue.html"
    return render(request, template, context)


@login_required
@role_required(User.Role.AGENT, User.Role.ADMIN)
def assume_ticket(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ticket = get_object_or_404(Ticket, pk=pk)
    change_field(ticket, "assignee", request.user, author=request.user)

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "ticket-assumed"
    return response
