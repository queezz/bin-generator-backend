from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from cadquery import exporters
from functools import lru_cache
from pathlib import Path
import tempfile
import tomllib

from bin_generator import make_bin

_VERSION_FALLBACK = "0.1.0"


def _read_app_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.is_file():
        return _VERSION_FALLBACK
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    ver = data.get("project", {}).get("version")
    if isinstance(ver, str) and ver.strip():
        return ver.strip()
    return _VERSION_FALLBACK


VERSION = _read_app_version()

CACHE_DIR = Path(tempfile.gettempdir()) / "stl_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_LIMIT = 100

# Bump when STL export semantics change (e.g. v1 used model.val() and dropped pattern solids).
_CACHE_FILE_VER = "v2"

print("STL cache directory:", CACHE_DIR)


def cache_path(x, y, h, wall, ears, use_ramp, texture):
    tag = "textured" if texture else "smooth"
    return CACHE_DIR / (
        f"bin-{_CACHE_FILE_VER}-{x}-{y}-{h}-w{wall:g}-ears{int(ears)}-ramp{int(use_ramp)}-{tag}.stl"
    )


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


@app.get("/info")
def info():
    return {
        "status": "ok",
        "version": VERSION,
        "name": "bin-generator-backend",
    }


@lru_cache(maxsize=128)
def build_stl(
    x: float,
    y: float,
    h: float,
    wall: float,
    ears: bool,
    use_ramp: bool,
    texture: bool,
) -> bytes:
    path = cache_path(x, y, h, wall, ears, use_ramp, texture)

    if path.exists():
        return path.read_bytes()

    model = make_bin(
        x=x,
        y=y,
        h=h,
        wall=wall,
        ears=ears,
        use_ramp=use_ramp,
        pattern=texture,
    )
    # Export the Workplane, not model.val(): val() can drop compound geometry
    # (e.g. wall pattern bumps), so textured bins looked identical to smooth.
    exporters.export(model, str(path), exporters.ExportTypes.STL)

    cleanup_cache()

    return path.read_bytes()


@app.get("/generate")
def generate(
    x: float = Query(50, ge=15, le=300),
    y: float = Query(100, ge=15, le=300),
    h: float = Query(30, ge=15, le=300),
    wall: float = Query(1.2, gt=0.4, le=2.99),
    ears: bool = Query(True),
    use_ramp: bool = Query(True),
    texture: bool = Query(False),
    name: bool = False,
):
    stl = build_stl(x, y, h, wall, ears, use_ramp, texture)

    if name:
        tag = "textured" if texture else "smooth"
        filename = (
            f"bin-{x:g}-{y:g}-{h:g}-w{wall:g}-ears{int(ears)}-ramp{int(use_ramp)}-{tag}.stl"
        )
    else:
        filename = "bin.stl"

    return Response(
        content=stl,
        media_type="model/stl",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
