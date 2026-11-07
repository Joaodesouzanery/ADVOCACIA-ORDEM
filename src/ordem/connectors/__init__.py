from .base import Conector, Dispositivo
from .planalto import PlanaltoConector, baixar_html, dividir_artigos, extrair_artigos, html_para_texto

__all__ = [
    "Conector",
    "Dispositivo",
    "PlanaltoConector",
    "baixar_html",
    "dividir_artigos",
    "extrair_artigos",
    "html_para_texto",
]
