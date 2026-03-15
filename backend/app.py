from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from cadquery import exporters
from functools import lru_cache
from pathlib import Path
import tempfile

from bin_generator import make_bin

CACHE_DIR = Path(tempfile.gettempdir()) / "stl_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_LIMIT = 100

print("STL cache directory:", CACHE_DIR)


def cache_path(x, y, h, ears):
    return CACHE_DIR / f"bin-{x}-{y}-{h}-ears{int(ears)}.stl"


def cleanup_cache():
    files = sorted(
        CACHE_DIR.glob("*.stl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    for f in files[CACHE_LIMIT:]:
        f.unlink(missing_ok=True)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=128)
def build_stl(x: float, y: float, h: float, ears: bool) -> bytes:
    path = cache_path(x, y, h, ears)

    if path.exists():
        return path.read_bytes()

    model = make_bin(x=x, y=y, h=h, ears=ears)
    shape = model.val() if hasattr(model, "val") else model

    exporters.export(shape, str(path), exporters.ExportTypes.STL)

    cleanup_cache()

    return path.read_bytes()


@app.get("/generate")
def generate(
    x: float = Query(50, ge=15, le=300),
    y: float = Query(100, ge=15, le=300),
    h: float = Query(30, ge=15, le=300),
    ears: bool = Query(True),
    name: bool = False,
):
    stl = build_stl(x, y, h, ears)

    if name:
        filename = f"bin-{x:g}-{y:g}-{h:g}-ears{int(ears)}.stl"
    else:
        filename = "bin.stl"

    return Response(
        content=stl,
        media_type="model/stl",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
