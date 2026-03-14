from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from cadquery import exporters
from functools import lru_cache
from pathlib import Path
import tempfile

from bin_generator import make_bin

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    name: bool = False,
):
    stl = build_stl(x, y, h)

    if name:
        filename = f"bin-{x:g}-{y:g}-{h:g}.stl"
    else:
        filename = "bin.stl"

    return Response(
        content=stl,
        media_type="model/stl",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
