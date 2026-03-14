from fastapi import FastAPI, Query
from fastapi.responses import Response
from cadquery import exporters
from functools import lru_cache
from pathlib import Path
import tempfile

from bin_generator import make_bin

app = FastAPI()


@lru_cache(maxsize=128)
def build_stl(x: float, y: float, h: float) -> bytes:
    model = make_bin(x=x, y=y, h=h)
    shape = model.val() if hasattr(model, "val") else model

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / f"bin-{x}-{y}-{h}.stl"
        exporters.export(shape, str(out_path), exporters.ExportTypes.STL)
        return out_path.read_bytes()


@app.get("/generate")
def generate(
    x: float = Query(50, gt=1),
    y: float = Query(100, gt=1),
    h: float = Query(30, gt=1),
) -> Response:
    stl = build_stl(x, y, h)
    return Response(
        content=stl,
        media_type="model/stl",
        headers={"Content-Disposition": f'attachment; filename="bin-{x}-{y}-{h}.stl"'},
    )
