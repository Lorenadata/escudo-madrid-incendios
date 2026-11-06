"""Exporta el contrato OpenAPI ejecutable a packages/contracts/openapi.json."""
import json
from pathlib import Path

from escudo_api.main import app

out = Path(__file__).resolve().parents[1] / "packages" / "contracts" / "openapi.json"
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OpenAPI -> {out} ({len(app.openapi()['paths'])} rutas)")
