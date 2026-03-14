# bin-generator-server

Web API that exposes the [bin-generator](https://github.com/queezz/bin-generator) CadQuery bin generator. Runs in Docker and is suitable for deployment to Google Cloud Run.

## Overview

- **GET /generate** — accepts dimensions `x`, `y`, `h` (defaults: 50, 100, 30), builds the bin with the installed generator, exports to STL, and returns the file as a download (`bin.stl`, `application/sla`).

Stack: Python 3.11, FastAPI, Uvicorn. Dependencies (including `bin-generator` from Git) are declared in `pyproject.toml` (PEP 621). No Poetry, no `requirements.txt`.

## Local development

```bash
cd bin-generator-server
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -e .
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8080
```

## Docker build

```bash
docker build -t bin-generator-server .
```

## Docker run

```bash
docker run -p 8080:8080 bin-generator-server
```

## Example request

Generate a bin with default dimensions:

```
http://localhost:8080/generate?x=50&y=100&h=30
```

Optional query parameters:

| Parameter | Type  | Default | Description   |
|----------|--------|---------|---------------|
| `x`      | float  | 50      | Bin length (X) |
| `y`      | float  | 100     | Bin width (Y)  |
| `h`      | float  | 30      | Bin height (Z) |

The response is an STL file download with filename `bin.stl` and content type `application/sla`.


## Try it local

```
cd bin-generator-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8080
```

Test download:
```
http://localhost:8080/generate?x=50&y=100&h=18&name=true
```
## Venv

```pws
python -m venv "$env:USERPROFILE/.venvs/server"
```
```pws
& "$env:USERPROFILE/.venvs/server/Scripts/Activate.ps1"
```