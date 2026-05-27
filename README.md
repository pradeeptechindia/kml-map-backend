# Project Setup

## Important Commands

```bash
source .venv/bin/activate
```

## Create Sample GeoTIFF (COG)

```bash
python -c "
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

arr = np.random.randint(0, 255, (3, 100, 100), dtype=np.uint8)
transform = from_bounds(88.45, 22.61, 88.47, 22.63, 100, 100)

with rasterio.open(
    'data/cogs/test.tif', 'w',
    driver='COG',
    height=100, width=100, count=3,
    dtype='uint8',
    crs=CRS.from_epsg(4326),
    transform=transform,
    tiled=True,
    blockxsize=256, blockysize=256,
) as dst:
    dst.write(arr)

print('Created test.tif')
"
```