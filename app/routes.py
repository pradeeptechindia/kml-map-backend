import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import rasterio
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from titiler.core.factory import TilerFactory

from app import registry

router = APIRouter(prefix="/cogs")


class UrlInput(BaseModel):
    url: str
    name: str | None = None
    acquisition_date: str | None = None


def _get_bounds(source: str) -> list[float]:
    with rasterio.open(source) as src:
        b = src.bounds
        return [b.left, b.bottom, b.right, b.top]


def _resolve_source(entry: dict) -> str:
    if entry["source"] == "upload":
        return entry["filepath"]
    return entry["url"]


def _cog_path(request: Request) -> str:
    """TiTiler calls this to get the file path or URL for a COG."""
    cog_id = request.path_params["cog_id"]
    entry = registry.get(cog_id)
    if not entry:
        raise HTTPException(404, "COG not found")
    return _resolve_source(entry)


# TiTiler factory — generates tiles, info, statistics, tilejson endpoints
tiler = TilerFactory(path_dependency=_cog_path, add_viewer=False)


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    name: str | None = None,
    acquisition_date: str | None = None,
):
    if not (file.filename and file.filename.lower().endswith((".tif", ".tiff"))):
        raise HTTPException(400, "Only .tif / .tiff files accepted")

    stem, suffix = file.filename.rsplit(".", 1)
    dest = registry.DATA_DIR / f"{stem}_{uuid.uuid4().hex[:8]}.{suffix}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        bounds = _get_bounds(str(dest))
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, f"Invalid GeoTIFF: {e}")

    return registry.add({
        "id": uuid.uuid4().hex[:8],
        "filename": file.filename,
        "source": "upload",
        "filepath": str(dest.absolute()),
        "url": None,
        "name": name or file.filename,
        "acquisition_date": acquisition_date,
        "bounds": bounds,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    })


@router.post("/register-url")
async def register_url(body: UrlInput):
    try:
        bounds = _get_bounds(body.url)
    except Exception as e:
        raise HTTPException(400, f"Cannot open remote COG: {e}")

    return registry.add({
        "id": uuid.uuid4().hex[:8],
        "filename": None,
        "source": "url",
        "filepath": None,
        "url": body.url,
        "name": body.name or body.url.split("/")[-1],
        "acquisition_date": body.acquisition_date,
        "bounds": bounds,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("")
async def list_cogs():
    return registry.read()


@router.get("/{cog_id}")
async def get_cog(cog_id: str):
    entry = registry.get(cog_id)
    if not entry:
        raise HTTPException(404, "Not found")
    return entry


# Mount TiTiler endpoints under /{cog_id}/tiler
# Gives us: /cogs/{id}/tiler/tiles/WebMercatorQuad/{z}/{x}/{y}.png
# Plus:     /cogs/{id}/tiler/info, /tilejson.json, /statistics, /preview, etc.
router.include_router(tiler.router, prefix="/{cog_id}/tiler")


@router.delete("/{cog_id}")
async def delete_cog(cog_id: str):
    entry = registry.remove(cog_id)
    if not entry:
        raise HTTPException(404, "Not found")
    if entry["filepath"]:
        Path(entry["filepath"]).unlink(missing_ok=True)
    return {"ok": True}