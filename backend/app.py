import tempfile
from pathlib import Path

import cadquery.exporters as exporters
from fastapi import FastAPI
from fastapi.responses import Response

from bin_generator import make_bin

app = FastAPI()


@app.get("/generate")
def generate(
    x: float = 50,
    y: float = 100,
    h: float = 30,
) -> Response:
    """Generate a bin model and return it as STL."""
    model = make_bin(x=x, y=y, h=h)
    if hasattr(model, "toCompound"):
        shape = model.toCompound()
    elif hasattr(model, "val"):
        shape = model.val()
    else:
        shape = model
    with tempfile.NamedTemporaryFile(
        suffix=".stl", delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        exporters.export(shape, str(tmp_path), exportType="STL")
        stl_bytes = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
    return Response(
        content=stl_bytes,
        media_type="application/sla",
        headers={"Content-Disposition": "attachment; filename=bin.stl"},
    )
