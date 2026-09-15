import datetime
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from assets.models import Asset, AssetStatus, AssetType
from knowledge.models import Article
from tickets.models import (
    BusinessHours,
    Category,
    Holiday,
    Macro,
    Priority,
    SLAPolicy,
    Status,
    SupportLevel,
    Ticket,
)

DEMO_PASSWORD = "nexus123"

DEPARTMENTS = [
    "Financeiro",
    "Recursos Humanos",
    "Comercial",
    "Operações",
    "Marketing",
    "Jurídico",
    "Atendimento",
]

FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Felipe", "Gabriela", "Hugo",
    "Isabela", "João", "Karina", "Lucas", "Marina", "Nathan", "Olívia",
    "Pedro", "Rafaela", "Sérgio", "Tatiana", "Vinícius", "Wesley", "Yasmin",
    "Camila", "Rodrigo",
]
LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Pereira", "Costa", "Almeida",
    "Ribeiro", "Carvalho", "Gomes", "Martins", "Rocha", "Araújo", "Dias",
]

CATEGORY_TITLES = {
    "Hardware": [
        "Notebook não liga mais",
        "Tela do monitor piscando",
        "Teclado com teclas falhando",
        "Notebook superaquecendo",
        "Bateria não segura carga",
        "Mouse parou de funcionar",
        "Notebook caiu e trincou a tela",
        "Fonte de alimentação queimada",
    ],
    "Software": [
        "Excel travando ao abrir planilhas grandes",
        "Erro ao instalar atualização do sistema",
        "Programa da folha de pagamento não abre",
        "Outlook fechando sozinho",
        "Erro de licença no pacote Office",
        "Sistema interno lento demais",
        "Aplicativo trava na tela de login",
    ],
    "Acesso/Senha": [
        "Reset de senha do AD",
        "Não consigo acessar minha conta",
        "Esqueci a senha do sistema financeiro",
        "Conta bloqueada após várias tentativas",
        "Preciso de acesso à pasta compartilhada do RH",
        "Acesso negado ao sistema de vendas",
    ],
    "Rede/VPN": [
        "VPN cai a cada 10 minutos",
        "Sem conexão com a rede da empresa",
        "Wi-Fi do 2º andar instável",
        "Não consigo conectar na VPN de casa",
        "Internet extremamente lenta",
        "Rede cabeada não funciona na minha sala",
    ],
    "E-mail": [
        "Não estou recebendo e-mails",
        "Caixa de entrada cheia",
        "E-mail marcado como spam indevidamente",
        "Erro ao enviar anexos grandes",
        "Assinatura de e-mail não está aparecendo",
    ],
    "Impressora": [
        "Impressora do 3º andar sem toner",
        "Impressora não é encontrada na rede",
        "Papel travando na impressora",
        "Impressão saindo borrada",
        "Impressora não imprime frente e verso",
    ],
}

ASSET_BRAND_MODELS = {
    AssetType.NOTEBOOK: ["Dell Latitude 5440", "Lenovo ThinkPad E14", "Dell Vostro 3520"],
    AssetType.DESKTOP: ["Dell OptiPlex 7020", "Lenovo ThinkCentre M70q"],
    AssetType.MONITOR: ["Dell P2422H 24\"", "LG 24MK430H"],
    AssetType.PERIFERICO: ["Teclado Logitech K120", "Mouse Logitech M170", "Headset JBL Quantum"],
    AssetType.CELULAR: ["Samsung Galaxy A54", "Motorola Moto G84"],
}

MACROS = [
    ("Senha redefinida", "Olá {{usuario}}, redefinimos a senha do chamado {{chamado}} conforme solicitado. Faça login e altere para uma senha de sua preferência no primeiro acesso."),
    ("Em análise", "Olá {{usuario}}, o chamado {{chamado}} está em análise pela nossa equipe. Retornamos em breve com uma atualização."),
    ("VPN reconfigurada", "Olá {{usuario}}, reconfiguramos seu acesso VPN referente ao chamado {{chamado}}. Peço que reinicie o notebook e teste a conexão."),
    ("Pedido de mais informações", "Olá {{usuario}}, para prosseguir com o chamado {{chamado}} preciso de mais detalhes: quando o problema começou e se ocorre sempre ou só às vezes."),
    ("Toner substituído", "Olá {{usuario}}, o toner da impressora referente ao chamado {{chamado}} foi substituído. Por favor confirme se a impressão normalizou."),
    ("Chamado resolvido", "Olá {{usuario}}, consideramos o chamado {{chamado}} resolvido. Se o problema voltar, é só reabrir por aqui."),
    ("Escalado para N2", "Chamado {{chamado}} escalado para o time N2 por {{agente}}. Segue o histórico para continuidade do atendimento."),
    ("Aguardando peça", "Olá {{usuario}}, o reparo do chamado {{chamado}} depende de uma peça que ainda não chegou. Assim que chegar, seguimos com o atendimento."),
    ("Acesso liberado", "Olá {{usuario}}, o acesso solicitado no chamado {{chamado}} já está liberado. Pode testar e nos avisar se algo não funcionar."),
    ("Reinicialização recomendada", "Olá {{usuario}}, aplicamos uma correção referente ao chamado {{chamado}}. Reinicie o equipamento para que a mudança tenha efeito."),
    ("Duplicado de outro chamado", "Este chamado parece estar relacionado a um problema já em andamento. Vinculamos ao chamado principal para acompanhamento único."),
    ("E-mail verificado", "Olá {{usuario}}, verificamos as configurações de e-mail referentes ao chamado {{chamado}} e corrigimos o problema encontrado."),
    ("Equipamento trocado", "Olá {{usuario}}, o equipamento com defeito do chamado {{chamado}} foi substituído. O antigo será recolhido para manutenção."),
    ("Sem reprodução do problema", "Olá {{usuario}}, não conseguimos reproduzir o problema relatado no chamado {{chamado}}. Nos avise se ele acontecer de novo, com data e hora."),
    ("Pesquisa de satisfação", "Olá {{usuario}}, o chamado {{chamado}} foi resolvido por {{agente}}. Poderia avaliar o atendimento? Isso nos ajuda a melhorar."),
]

ARTICLES = [
    ("Como redefinir minha senha de rede", "Acesso/Senha"),
    ("Como conectar na VPN corporativa", "Rede/VPN"),
    ("O que fazer quando o Outlook trava", "Software"),
    ("Como liberar espaço na caixa de e-mail", "E-mail"),
    ("Passo a passo para configurar a impressora do andar", "Impressora"),
    ("Notebook não liga: primeiros passos antes de abrir chamado", "Hardware"),
    ("Como solicitar acesso a uma pasta compartilhada", "Acesso/Senha"),
    ("Wi-Fi instável: como testar antes de abrir chamado", "Rede/VPN"),
    ("Erro de licença do Office: solução rápida", "Software"),
    ("Como enviar anexos grandes por e-mail", "E-mail"),
    ("Impressora não aparece na rede: checklist", "Impressora"),
    ("Bateria do notebook descarregando rápido", "Hardware"),
    ("Sistema interno lento: o que verificar antes de abrir chamado", "Software"),
    ("Como funciona o bloqueio de conta após tentativas erradas", "Acesso/Senha"),
    ("VPN caindo em casa: checklist de rede doméstica", "Rede/VPN"),
]

NATIONAL_HOLIDAYS_2026 = [
    (datetime.date(2026, 1, 1), "Confraternização Universal"),
    (datetime.date(2026, 4, 21), "Tiradentes"),
    (datetime.date(2026, 5, 1), "Dia do Trabalho"),
    (datetime.date(2026, 9, 7), "Independência do Brasil"),
    (datetime.date(2026, 10, 12), "Nossa Senhora Aparecida"),
    (datetime.date(2026, 11, 2), "Finados"),
    (datetime.date(2026, 11, 15), "Proclamação da República"),
    (datetime.date(2026, 12, 25), "Natal"),
]


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração (usuários, chamados, base de conhecimento, ativos)."

    def handle(self, *args, **options):
        random.seed(42)

        with transaction.atomic():
            self._reset()
            categories = self._create_categories()
            self._create_sla_policies()
            self._create_business_hours()
            self._create_holidays()
            admin = self._create_admin()
            agents = self._create_agents()
            users = self._create_users()
            self._create_macros(admin)
            self._create_articles(categories)
            assets = self._create_assets(users + agents)
            self._create_tickets(categories, users, agents)

        self.stdout.write(self.style.SUCCESS("Seed concluído."))
        self.stdout.write("")
        self.stdout.write(f"Contas de demonstração (senha para todas: {DEMO_PASSWORD}):")
        self.stdout.write(f"  Admin:  {admin.username}")
        for agent in agents:
            self.stdout.write(f"  Agente: {agent.username} ({agent.support_level})")
        self.stdout.write(f"  Usuário: {users[0].username} (+ {len(users) - 1} outros)")
        self.stdout.write("")
        self.stdout.write(
            f"{Ticket.objects.count()} chamados, {len(assets)} ativos, "
            f"{Article.objects.count()} artigos, {Macro.objects.count()} macros."
        )

    def _reset(self):
        Ticket.objects.all().delete()
        Macro.objects.all().delete()
        Article.objects.all().delete()
        Asset.objects.all().delete()
        Holiday.objects.all().delete()
        BusinessHours.objects.all().delete()
        SLAPolicy.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(username="admin").delete()

    def _create_categories(self):
        return {
            name: Category.objects.create(name=name) for name in CATEGORY_TITLES
        }

    def _create_sla_policies(self):
        minutes = {
            Priority.BAIXA: (480, 2880),
            Priority.MEDIA: (240, 1440),
            Priority.ALTA: (60, 480),
            Priority.CRITICA: (30, 240),
        }
        for priority, (first_response, resolution) in minutes.items():
            SLAPolicy.objects.create(
                priority=priority,
                first_response_minutes=first_response,
                resolution_minutes=resolution,
            )

    def _create_business_hours(self):
        for weekday in range(5):  # segunda a sexta
            BusinessHours.objects.create(
                weekday=weekday,
                start_time=datetime.time(8, 0),
                end_time=datetime.time(18, 0),
            )

    def _create_holidays(self):
        for date, name in NATIONAL_HOLIDAYS_2026:
            Holiday.objects.create(date=date, name=name)

    def _create_admin(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@nexusdesk.com",
            password=DEMO_PASSWORD,
            first_name="Admin",
            last_name="Nexus",
        )
        admin.role = User.Role.ADMIN
        admin.department = "TI"
        admin.save(update_fields=["role", "department"])
        return admin

    def _create_agents(self):
        agents_spec = [
            ("agente.n1.ana", "Ana", "Ferreira", User.SupportLevel.N1),
            ("agente.n1.bruno", "Bruno", "Tavares", User.SupportLevel.N1),
            ("agente.n2.carla", "Carla", "Nogueira", User.SupportLevel.N2),
            ("agente.n2.diego", "Diego", "Lopes", User.SupportLevel.N2),
        ]
        agents = []
        for username, first, last, level in agents_spec:
            agent = User.objects.create_user(
                username=username,
                email=f"{username}@nexusdesk.com",
                password=DEMO_PASSWORD,
                first_name=first,
                last_name=last,
                role=User.Role.AGENT,
                department="TI",
                support_level=level,
            )
            agents.append(agent)
        return agents

    def _create_users(self):
        users = []
        pairs = list(zip(FIRST_NAMES, LAST_NAMES * 2, strict=False))
        for i, (first, last) in enumerate(pairs[:20]):
            username = f"{first.lower()}.{last.lower()}"
            department = DEPARTMENTS[i % len(DEPARTMENTS)]
            user = User.objects.create_user(
                username=username,
                email=f"{username}@empresa.com",
                password=DEMO_PASSWORD,
                first_name=first,
                last_name=last,
                role=User.Role.USER,
                department=department,
            )
            users.append(user)
        return users

    def _create_macros(self, admin):
        for title, body in MACROS:
            Macro.objects.create(title=title, body_template=body, created_by=admin)

    def _create_articles(self, categories):
        for title, category_name in ARTICLES:
            Article.objects.create(
                title=title,
                content=(
                    f"# {title}\n\nPasso a passo resumido para resolver isso sem "
                    "precisar abrir chamado. Se o problema persistir, abra um "
                    "chamado descrevendo o que já foi tentado."
                ),
                category=categories[category_name],
                views=random.randint(5, 400),
                helpful_votes=random.randint(0, 80),
            )

    def _create_assets(self, owners):
        now = timezone.now().date()
        assets = []
        for i in range(1, 51):
            asset_type = random.choice(list(AssetType.values))
            purchased_at = now - datetime.timedelta(days=random.randint(30, 1200))
            warranty_years = random.choice([1, 1, 2, 3])
            warranty_until = purchased_at + datetime.timedelta(days=365 * warranty_years)
            # Força uma fatia de garantias vencendo nos próximos 30 dias, e
            # outra fatia já vencida — dados úteis pro alerta de garantia (Fase 3).
            if i % 10 == 0:
                warranty_until = now + datetime.timedelta(days=random.randint(1, 30))
            elif i % 11 == 0:
                warranty_until = now - datetime.timedelta(days=random.randint(1, 200))

            status = random.choices(
                list(AssetStatus.values),
                weights=[70, 15, 10, 5],
            )[0]
            owner = random.choice(owners) if status == AssetStatus.EM_USO else None

            assets.append(
                Asset.objects.create(
                    tag=f"AT-{i:04d}",
                    type=asset_type,
                    brand_model=random.choice(ASSET_BRAND_MODELS[asset_type]),
                    serial_number=f"SN{random.randint(100000, 999999)}",
                    owner=owner,
                    status=status,
                    purchased_at=purchased_at,
                    warranty_until=warranty_until,
                )
            )
        return assets

    def _create_tickets(self, categories, users, agents):
        n1_agents = [a for a in agents if a.support_level == User.SupportLevel.N1]
        n2_agents = [a for a in agents if a.support_level == User.SupportLevel.N2]
        now = timezone.now()

        priority_weights = {
            Priority.BAIXA: 35,
            Priority.MEDIA: 40,
            Priority.ALTA: 20,
            Priority.CRITICA: 5,
        }
        priorities = list(priority_weights.keys())
        priority_probs = list(priority_weights.values())

        for _ in range(250):
            category_name = random.choice(list(CATEGORY_TITLES.keys()))
            category = categories[category_name]
            title = random.choice(CATEGORY_TITLES[category_name])
            requester = random.choice(users)
            priority = random.choices(priorities, weights=priority_probs)[0]

            age_days = random.randint(0, 90)
            created_at = now - datetime.timedelta(
                days=age_days, hours=random.randint(0, 23), minutes=random.randint(0, 59)
            )

            is_escalated = random.random() < 0.15
            support_level = SupportLevel.N2 if is_escalated else SupportLevel.N1
            level_agents = n2_agents if is_escalated else n1_agents

            # Chamados mais antigos têm mais chance de já estarem encerrados.
            if age_days > 20:
                status = random.choices(
                    list(Status.values),
                    weights=[3, 5, 5, 15, 65, 7],
                )[0]
            elif age_days > 5:
                status = random.choices(
                    list(Status.values),
                    weights=[10, 25, 15, 25, 20, 5],
                )[0]
            else:
                status = random.choices(
                    list(Status.values),
                    weights=[45, 35, 15, 4, 1, 0],
                )[0]

            assignee = None
            first_response_at = None
            resolved_at = None
            closed_at = None

            if status != Status.ABERTO:
                assignee = random.choice(level_agents)
                first_response_at = created_at + datetime.timedelta(
                    minutes=random.randint(10, 600)
                )

            if status in (Status.RESOLVIDO, Status.FECHADO, Status.REABERTO):
                resolved_at = first_response_at + datetime.timedelta(
                    minutes=random.randint(30, 4000)
                )
                if resolved_at > now:
                    resolved_at = now

            if status == Status.FECHADO:
                closed_at = resolved_at + datetime.timedelta(hours=random.randint(1, 96))
                if closed_at > now:
                    closed_at = now

            ticket = Ticket(
                requester=requester,
                assignee=assignee,
                category=category,
                title=title,
                description=(
                    f"Usuário relata: {title.lower()}. "
                    "Favor verificar e retornar com uma solução ou próximos passos."
                ),
                status=status,
                priority=priority,
                support_level=support_level,
            )
            ticket.save()
            Ticket.objects.filter(pk=ticket.pk).update(
                created_at=created_at,
                first_response_at=first_response_at,
                resolved_at=resolved_at,
                closed_at=closed_at,
            )
