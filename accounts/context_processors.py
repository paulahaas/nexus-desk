from django.conf import settings


def demo_mode(request):
    return {"demo_mode": settings.DEMO_MODE}
