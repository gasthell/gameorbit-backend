from fastapi import APIRouter
from django.forms.models import model_to_dict
from core.models import Tariff, MainPageGame

router = APIRouter()

@router.get("/")
def info():
    return {"detail":"Not Found"}

@router.get("/tariffs/")
def get_tariffs():
    tariffs = Tariff.objects.all()
    result = []
    for t in tariffs:
        d = model_to_dict(t)
        # Add features as a list of feature names (or dicts if you want more detail)
        d['features'] = [f.name for f in t.features.all()]
        result.append(d)
    return result

@router.get("/main-page-games/")
def get_main_page_games():
    games = MainPageGame.objects.all().order_by('order')
    result = []
    for g in games:
        d = model_to_dict(g)
        # Convert picture field to URL or None
        d['picture'] = g.picture.url if g.picture else None
        result.append(d)
    return result