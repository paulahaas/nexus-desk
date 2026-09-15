# Nexus Desk

> 🚧 Em construção. Este README cresce junto com o projeto, fase a fase — a versão completa (screenshots, GIF, roadmap, diagramas) chega ao final da Fase 1.

Helpdesk de TI interno, pensado como uma ferramenta de service desk de verdade (papéis, SLA com horário comercial, escalonamento, classificação automática por IA, base de conhecimento), não um CRUD de portfólio.

Django 5 + HTMX + Alpine.js no front (sem SPA), PostgreSQL, Tailwind CSS, scikit-learn para a classificação de chamados.

## Rodar localmente

```bash
cp .env.example .env
docker compose up
```

Acesse `http://localhost:8000/health` para confirmar que o app e o banco estão de pé.

## Testes

```bash
docker compose run --rm web pytest
docker compose run --rm web ruff check .
```
