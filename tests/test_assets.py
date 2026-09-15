import pytest
from django.db import IntegrityError, transaction

from assets.models import Asset, AssetStatus, AssetType


@pytest.mark.django_db
def test_asset_str_includes_tag_and_model():
    asset = Asset.objects.create(
        tag="AT-0001",
        type=AssetType.NOTEBOOK,
        brand_model="Dell Latitude 5440",
        status=AssetStatus.ESTOQUE,
    )

    assert str(asset) == "AT-0001 — Dell Latitude 5440"


@pytest.mark.django_db
def test_asset_tag_is_unique():
    Asset.objects.create(tag="AT-0002", type=AssetType.MONITOR, brand_model="LG 24MK430H")

    with pytest.raises(IntegrityError), transaction.atomic():
        Asset.objects.create(tag="AT-0002", type=AssetType.MONITOR, brand_model="Outro")
