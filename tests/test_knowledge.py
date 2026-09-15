import pytest

from knowledge.models import Article


@pytest.mark.django_db
def test_slug_is_generated_from_title():
    article = Article.objects.create(
        title="Como redefinir minha senha de rede",
        content="# Passo a passo",
    )

    assert article.slug == "como-redefinir-minha-senha-de-rede"


@pytest.mark.django_db
def test_explicit_slug_is_kept():
    article = Article.objects.create(
        title="Outro título", content="conteúdo", slug="slug-customizado"
    )

    assert article.slug == "slug-customizado"
