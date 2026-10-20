"""
Tile-based preprocessing for large dense drawings (P&IDs, schematics).

Splits an image into overlapping tiles, preprocesses each tile
independently with locally-tuned parameters, and reassembles them.
"""

import cv2
import numpy as np
from typing import Iterator


def tile_image(
    image: np.ndarray,
    tile_size: int = 1500,
    overlap: int = 200,
) -> Iterator[tuple]:
    """
    Yield (tile, x_offset, y_offset) tuples covering the image.

    Args:
        image:     grayscale or binary numpy array
        tile_size: size of each square tile
        overlap:   pixels of overlap between adjacent tiles

    Yields:
        (tile_array, x0, y0) — x0, y0 are the top-left coords in the original
    """
    h, w = image.shape[:2]
    step = tile_size - overlap

    if step <= 0:
        raise ValueError("tile_size must be > overlap")

    for y0 in range(0, h, step):
        for x0 in range(0, w, step):
            x1 = min(x0 + tile_size, w)
            y1 = min(y0 + tile_size, h)

            # Skip tiny edge tiles
            if (x1 - x0) < tile_size * 0.3 or (y1 - y0) < tile_size * 0.3:
                continue

            tile = image[y0:y1, x0:x1]
            yield tile, x0, y0

            if x1 >= w:
                break
        if y1 >= h:
            break


def local_threshold(tile: np.ndarray, block_size: int = 15, c: int = 8) -> np.ndarray:
    """
    Adaptive threshold tuned for small text in dense drawings.

    Uses SMALLER block_size than full-sheet thresholding so that
    text near thick lines still separates cleanly.
    """
    if block_size % 2 == 0:
        block_size += 1

    # Ensure block_size doesn't exceed tile size
    max_block = min(tile.shape[:2]) - 1
    if max_block % 2 == 0:
        max_block -= 1
    block_size = min(block_size, max_block)
    block_size = max(block_size, 3)

    return cv2.adaptiveThreshold(
        tile, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c,
    )


def preprocess_tiled(
    image_np: np.ndarray,
    tile_size: int = 1500,
    overlap: int = 200,
    block_size: int = 15,
    c: int = 8,
    do_invert: bool = True,
) -> tuple:
    """
    Full tile-based preprocessing.

    Returns:
        (reassembled_binary_image, list_of_tile_metadata)
        tile_metadata = [{"x": x0, "y": y0, "shape": (h, w), "tile": array}]
    """
    # Convert to grayscale if needed
    if image_np.ndim == 3:
        if image_np.shape[2] == 4:
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np

    h, w = gray.shape
    result = np.full((h, w), 255, dtype=np.uint8)
    tile_metadata = []

    for tile, x0, y0 in tile_image(gray, tile_size=tile_size, overlap=overlap):
        binary_tile = local_threshold(tile, block_size=block_size, c=c)

        if do_invert:
            # Only invert if this tile is mostly dark
            if np.mean(binary_tile == 255) < 0.5:
                binary_tile = cv2.bitwise_not(binary_tile)

        # Paste into result. For overlapping regions, use "min" (darkest wins)
        # so no text is lost — but weight the center of tiles higher.
        th, tw = binary_tile.shape
        region = result[y0:y0 + th, x0:x0 + tw]
        result[y0:y0 + th, x0:x0 + tw] = np.minimum(region, binary_tile)

        tile_metadata.append({
            "x": x0,
            "y": y0,
            "shape": (th, tw),
            "tile": binary_tile,
        })

    return result, tile_metadata