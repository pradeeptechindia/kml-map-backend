import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from rio_tiler.errors import TileOutsideBounds

from app.routes import router

app = FastAPI(title="KML Map Tile Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ["KML_MAP_CORS_ORIGINS"].split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TileOutsideBounds)
async def tile_out_of_bounds(request: Request, exc: TileOutsideBounds):
    return Response(status_code=204)


app.include_router(router)