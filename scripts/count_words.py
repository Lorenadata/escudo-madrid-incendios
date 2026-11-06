"""Cuenta las palabras del resumen de preselección (límite 100)."""
import re
import sys
from pathlib import Path

doc = Path(__file__).resolve().parents[1] / "docs" / "pitch" / "resumen-preseleccion.md"
text = re.search(r"<!-- RESUMEN:INICIO -->(.*?)<!-- RESUMEN:FIN -->", doc.read_text(encoding="utf-8"), re.S).group(1)
n = len(re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+(?:[-'][\wÁÉÍÓÚÜÑáéíóúüñ]+)*", text))
print(f"{n} palabras")
sys.exit(0 if n <= 100 else 1)
