from datetime import datetime
from pytz import timezone

BRASILIA_TZ = timezone('America/Sao_Paulo')

def get_brasilia_now():
    """
    Retorna o datetime atual em horário de Brasília (timezone-aware).
    """
    return datetime.now(BRASILIA_TZ)

def get_formatted_now():
    """
    Retorna a hora atual formatada como string 'DD/MM/YYYY HH:MM' em horário de Brasília.
    """
    now = get_brasilia_now()
    return now.strftime('%Y-%m-%d %H:%M')

def get_brasilia_date():
    """
    Retorna a data de hoje em horário de Brasília (timezone-aware).
    """
    now = get_brasilia_now()
    return now.date()
