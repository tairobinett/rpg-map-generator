import numpy as np
from PIL import Image, ImageDraw
from opensimplex import OpenSimplex, noise2array
from scipy.interpolate import splprep, splev
import random
import math
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Set, Optional


class TerrainType:
    WATER = 0
    SAND = 1
    GRASS = 2
    FOREST = 3
    HILL = 4
    MOUNTAIN = 5
    FLOOR = 6


@dataclass
class Building:
    rooms: List[Tuple[int, int, int, int]] = field(default_factory=list)
    interior_tiles: Set[Tuple[int, int]] = field(default_factory=set)
    wall_segments: Set[Tuple[Tuple[int,int],Tuple[int,int]]] = field(default_factory=set)
    entrance: Optional[Tuple[int, int, str]] = None
    doors: List[Tuple[int, int, str]] = field(default_factory=list)
    # doors: list of (row, col, side) – one per inter-room shared wall.
    # the wall segment for each door is removed from wall_segments.


class TerrainGenerator:
    def __init__(self, width, height, seed, tile_size=128, texture_folder=None, foliage_folder=None, building_folder=None):
        self.width = width
        self.height = height
        self.seed = seed
        self.tile_size = tile_size
        self.texture_folder = texture_folder
        self.foliage_folder = foliage_folder
        self.building_folder = building_folder
        self.foliage_tiles = {}   # dict: subdir_name -> set of (row, col) tiles
        self.foliage_assets = {}  # dict: subdir_name -> list of filenames in that subdir
        self.building: Optional[Building] = None

        random.seed(seed)
        np.random.seed(seed)
        self.noise = OpenSimplex(seed)

        self.terrain_grid = np.zeros((height, width), dtype=int)

        # Load textures if folder provided
        self.textures = {}
        if texture_folder:
            self.load_textures()


    def load_textures(self):
        import os

        terrain_texture_files = {
            TerrainType.WATER: 'water.png',
            TerrainType.GRASS: 'grass.png',
            TerrainType.SAND:  'sand.png',
            TerrainType.FLOOR: 'floor.png',
        }

        for terrain_type, filename in terrain_texture_files.items():
            filepath = os.path.join(self.texture_folder, filename)
            if os.path.exists(filepath):
                texture = Image.open(filepath).convert('RGB')
                # Resize texture to be at least as large as tile_size
                if texture.width < self.tile_size or texture.height < self.tile_size:
                    new_size = max(self.tile_size, texture.width, texture.height)
                    tiled = Image.new('RGB', (new_size, new_size))
                    for y in range(0, new_size, texture.height):
                        for x in range(0, new_size, texture.width):
                            tiled.paste(texture, (x, y))
                    texture = tiled
                self.textures[terrain_type] = texture
            else:
                print(f"Warning: Texture not found: {filepath}")


    def _generate_noise_map(self, scale=0.1, octaves=4, x_offset=0, y_offset=0):
        # Generate a normalised multi-octave noise map with given offsets
        noise_map = np.zeros((self.height, self.width))
        for octave in range(octaves):
            frequency = 2 ** octave
            amplitude = 1 / (2 ** octave)
            xs = np.arange(self.width) * scale * frequency + x_offset
            ys = np.arange(self.height) * scale * frequency + y_offset
            noise_map += noise2array(xs, ys) * amplitude
        # Normalize to 0-1 range
        noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
        return noise_map

    def generate_terrain(self, river_width, foliage_density, foliage_coverage, scale=0.1, octaves=4,
                         num_rooms=4, min_room_size=3, max_room_size=6):
        self.terrain_grid.fill(TerrainType.GRASS)

        # Generate smooth pixel-space river mask and stamp water tiles from it
        river_pixel_mask, river_tiles = self.generate_river(river_width)
        self.river_pixel_mask = river_pixel_mask  # store for rendering

        for tile in list(river_tiles):
            self.terrain_grid[tile[1], tile[0]] = TerrainType.WATER

        # Generate building
        self.building = self.generate_building(
            num_rooms=num_rooms,
            min_room_size=min_room_size,
            max_room_size=max_room_size,
            river_tiles=river_tiles,
        )
        for (row, col) in self.building.interior_tiles:
            self.terrain_grid[row, col] = TerrainType.FLOOR

        # Per-subdirectory noise maps
        # Each subdirectory = one foliage type with its own noise map
        # Files placed directly in foliage_folder (no subdir) are ignored
        self.foliage_tiles = {}  # dict: subdir_name -> set of (row, col)
        self.foliage_assets = {}  # dict: subdir_name -> list of filenames in that subdir

        if self.foliage_folder and os.path.isdir(self.foliage_folder):
            # get subdirectories (sorted for determinism)
            subdirs = sorted([
                d for d in os.listdir(self.foliage_folder)
                if os.path.isdir(os.path.join(self.foliage_folder, d))
            ])

            # Give each subdirectory its own independent noise offset
            rng = random.Random(self.seed)
            subdir_offsets = {
                subdir: (rng.randint(0, 1_000_000), rng.randint(0, 1_000_000))
                for subdir in subdirs
            }

            for x, subdir in enumerate(subdirs):
                subdir_path = os.path.join(self.foliage_folder, subdir)
                files = sorted([
                    f for f in os.listdir(subdir_path)
                    if os.path.isfile(os.path.join(subdir_path, f))
                ])
                if not files:
                    continue

                self.foliage_assets[subdir] = files

                x_off, y_off = subdir_offsets[subdir]
                noise_map = self._generate_noise_map(scale=scale, octaves=octaves,
                                                     x_offset=x_off, y_offset=y_off)
                candidate_tiles = self.get_tiles_above_threshold(noise_map, foliage_coverage[x])

                tile_set = set()
                local_rng = random.Random(self.seed ^ hash(subdir))
                for tile in candidate_tiles:
                    row, col = int(tile[0]), int(tile[1])
                    if self.terrain_grid[row, col] != TerrainType.GRASS:
                        continue
                    # Exclude tiles inside river mask
                    center_px = col * self.tile_size + self.tile_size // 2
                    center_py = row * self.tile_size + self.tile_size // 2
                    if (0 <= center_py < river_pixel_mask.shape[0] and
                            0 <= center_px < river_pixel_mask.shape[1]):
                        if river_pixel_mask[center_py, center_px]:
                            continue
                    if local_rng.random() <= foliage_density[x]:
                        tile_set.add((row, col))

                self.foliage_tiles[subdir] = tile_set

        return self.terrain_grid

    # building generation
    def generate_building(self, num_rooms: int, min_room_size: int, max_room_size: int,
                          river_tiles: set) -> Building:
        bld_rng = random.Random(self.seed ^ 0xB01D1)

        margin = 1  # tile border kept clear around the whole map

        # river_tiles are stored as (col, row) by generate_river — normalise
        # to (row, col) and expand by 1-tile buffer so rooms don't touch water.
        forbidden: Set[Tuple[int,int]] = set()
        for (col, row) in river_tiles:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.height and 0 <= nc < self.width:
                        forbidden.add((nr, nc))

        rooms: List[Tuple[int,int,int,int]] = []

        # place first room
        for _ in range(200):
            w = bld_rng.randint(min_room_size, max_room_size)
            h = bld_rng.randint(min_room_size, max_room_size)
            col = bld_rng.randint(margin, self.width  - w - margin)
            row = bld_rng.randint(margin, self.height - h - margin)
            if not self._room_conflicts(col, row, w, h, rooms, forbidden):
                rooms.append((col, row, w, h))
                break

        if not rooms:
            # could not place even one room
            return Building()

        # accrete additional rooms
        for _ in range(num_rooms - 1):
            placed = False
            # Shuffle attempt order so result varies
            room_order = list(range(len(rooms)))
            bld_rng.shuffle(room_order)
            for ri in room_order:
                parent = rooms[ri]
                new_room = self._try_attach_room(
                    parent, rooms, forbidden, bld_rng,
                    min_room_size, max_room_size, margin
                )
                if new_room:
                    rooms.append(new_room)
                    placed = True
                    break

        # collect interior tiles
        interior: Set[Tuple[int,int]] = set()
        # (row, col) -> room index
        tile_room: dict = {}
        for idx, (col, row, w, h) in enumerate(rooms):
            for r in range(row, row + h):
                for c in range(col, col + w):
                    interior.add((r, c))
                    tile_room[(r, c)] = idx

        # build wall segments (grid-line coords)
        # Segments appear on: outer boundary AND shared edges between rooms.
        walls = self._compute_wall_segments(interior, tile_room)

        # pick entrance on the first room's outermost wall
        entrance = self._pick_entrance(rooms[0], interior, walls, bld_rng)

        # cut one door opening per inter-room shared wall
        doors = self._pick_inter_room_doors(rooms, tile_room, walls, bld_rng)

        return Building(
            rooms=rooms,
            interior_tiles=interior,
            wall_segments=walls,
            entrance=entrance,
            doors=doors,
        )

    def _room_conflicts(self, col, row, w, h,
                        existing_rooms, forbidden_tiles) -> bool:
        # return true if overlaps existing room or forbidden tile
        for r in range(row, row + h):
            for c in range(col, col + w):
                if (r, c) in forbidden_tiles:
                    return True
        for (ec, er, ew, eh) in existing_rooms:
            # Rectangles overlap if they are not separated on any axis
            if not (col >= ec + ew or col + w <= ec or
                    row >= er + eh or row + h <= er):
                return True
        return False

    def _try_attach_room(self, parent, all_rooms, forbidden, rng,
                         min_size, max_size, margin) -> Optional[Tuple[int,int,int,int]]:
        pc, pr, pw, ph = parent
        sides = ['N', 'S', 'E', 'W']
        rng.shuffle(sides)

        for side in sides:
            for _ in range(40):
                if side in ('N', 'S'):
                    # New room shares a horizontal wall: same width axis
                    nw = rng.randint(min_size, max_size)
                    nh = rng.randint(min_size, max_size)
                    # Overlap on the shared wall axis: at least min_size tiles
                    overlap = rng.randint(min_size, max(min_size, min(pw, nw)))
                    # Align: shared wall tiles start at nc, nc+overlap-1
                    nc = rng.randint(pc - nw + overlap, pc + pw - overlap)
                    if side == 'N':
                        # new room is above
                        nr = pr - nh
                    else:
                        # new room is below
                        nr = pr + ph
                else: # E/W
                    nw = rng.randint(min_size, max_size)
                    nh = rng.randint(min_size, max_size)
                    overlap = rng.randint(min_size, max(min_size, min(ph, nh)))
                    nr = rng.randint(pr - nh + overlap, pr + ph - overlap)
                    if side == 'W':
                        nc = pc - nw
                    else:
                        nc = pc + pw

                # Bounds check
                if (nc < margin or nr < margin or
                        nc + nw > self.width  - margin or
                        nr + nh > self.height - margin):
                    continue

                if not self._room_conflicts(nc, nr, nw, nh, all_rooms, forbidden):
                    return (nc, nr, nw, nh) # col, row, w, h
        return None

    def _compute_wall_segments(
            self, interior: Set[Tuple[int,int]], tile_room: dict
    ) -> Set[Tuple[Tuple[int,int],Tuple[int,int]]]:
        """
        Return wall segments for:
          - the outer boundary of the building (neighbour is outside)
          - shared edges between two *different* rooms (room dividers)

        Grid point (gx, gy) maps to pixel (gx * tile_size, gy * tile_size).
        """
        # return wall segments for outer boundary of building and shared edges of different rooms
        walls: Set[Tuple[Tuple[int,int],Tuple[int,int]]] = set()
        for (row, col) in interior:
            my_room = tile_room[(row, col)]

            def _want_wall(neighbour):
                if neighbour not in interior:
                    return True  # outer boundary
                return tile_room[neighbour] != my_room  # room divider

            # North edge
            if _want_wall((row - 1, col)):
                walls.add(((col, row),   (col+1, row)))
            # South edge
            if _want_wall((row + 1, col)):
                walls.add(((col, row+1), (col+1, row+1)))
            # West edge
            if _want_wall((row, col - 1)):
                walls.add(((col, row),   (col, row+1)))
            # East edge
            if _want_wall((row, col + 1)):
                walls.add(((col+1, row), (col+1, row+1)))
        return walls

    def _pick_entrance(self, first_room, interior, walls, rng
                       ) -> Optional[Tuple[int,int,str]]:
        # pick one wall segment on outside of first room
        # remove chosen wall segment from walls set
        # returns (row, col, side) for entrance tile
        fc, fr, fw, fh = first_room
        # Collect candidate (tile, side, segment) triples from outer edges
        candidates = []
        for row in range(fr, fr + fh):
            for col in range(fc, fc + fw):
                for side, seg in [
                    ('N', ((col, row),   (col+1, row))),
                    ('S', ((col, row+1), (col+1, row+1))),
                    ('W', ((col, row),   (col, row+1))),
                    ('E', ((col+1, row), (col+1, row+1))),
                ]:
                    if seg in walls:
                        # It's an outer wall segment
                        outside_tile = {
                            'N': (row - 1, col),
                            'S': (row + 1, col),
                            'W': (row, col - 1),
                            'E': (row, col + 1),
                        }[side]
                        if outside_tile not in interior:
                            candidates.append((row, col, side, seg))

        if not candidates:
            return None

        row, col, side, seg = rng.choice(candidates)
        walls.discard(seg)
        return (row, col, side)

    def _pick_inter_room_doors(self, rooms, tile_room, walls, rng
                               ) -> List[Tuple[int,int,str]]:
        # for each pair of adjacent rooms, collect wall aegments on shared boundary, pick one, remove from walls set, replace with door
        # returns list of (row, col, side) door descriptors, 1 per adjacent room pair.
        # side is based on lower index room's perspective
        doors: List[Tuple[int,int,str]] = []

        num_rooms = len(rooms)
        # Find all adjacent room pairs (each pair handled once)
        for i in range(num_rooms):
            for j in range(i + 1, num_rooms):
                # Collect segments that sit between room i and room j
                shared_segs = []
                ci, ri, wi, hi = rooms[i]
                for row in range(ri, ri + hi):
                    for col in range(ci, ci + wi):
                        for side, seg, nbr in [
                            ('N', ((col, row),   (col+1, row)),   (row-1, col)),
                            ('S', ((col, row+1), (col+1, row+1)), (row+1, col)),
                            ('W', ((col, row),   (col, row+1)),   (row, col-1)),
                            ('E', ((col+1, row), (col+1, row+1)), (row, col+1)),
                        ]:
                            if seg in walls and tile_room.get(nbr) == j:
                                shared_segs.append((row, col, side, seg))

                if not shared_segs:
                    continue  # rooms i and j don't share a wall

                row, col, side, seg = rng.choice(shared_segs)
                walls.discard(seg)
                doors.append((row, col, side))

        return doors


    def noise_to_terrain(self, noise_map):
        terrain = np.zeros_like(noise_map, dtype=int)

        # Thresholds for different terrain types
        terrain[noise_map < 0.3] = TerrainType.WATER
        terrain[(noise_map >= 0.3) & (noise_map < 0.35)] = TerrainType.SAND
        terrain[(noise_map >= 0.35) & (noise_map < 0.55)] = TerrainType.GRASS
        terrain[(noise_map >= 0.55) & (noise_map < 0.7)] = TerrainType.FOREST
        terrain[(noise_map >= 0.7) & (noise_map < 0.85)] = TerrainType.HILL
        terrain[noise_map >= 0.85] = TerrainType.MOUNTAIN

        return terrain

    def get_tiles_above_threshold(self, noise_map, threshold): 
        return np.argwhere(noise_map > threshold)

    def render_to_image(self, show_grid=True):
        img_width = self.width * self.tile_size
        img_height = self.height * self.tile_size

        colors = {
            TerrainType.WATER:      (65, 105, 225),
            TerrainType.SAND:       (238, 214, 175),
            TerrainType.GRASS:      (107, 142, 35),
            TerrainType.FOREST:     (34, 139, 34),
            TerrainType.HILL:       (139, 90, 43),
            TerrainType.MOUNTAIN:   (105, 105, 105),
            TerrainType.FLOOR:      (180, 160, 130),
        }

        # Render all tiles as grass first
        color_array = np.zeros((img_height, img_width, 3), dtype=np.uint8)
        for terrain_type, color in colors.items():
            mask = (self.terrain_grid == terrain_type)
            rows, cols = np.where(mask)
            for row, col in zip(rows, cols):
                px, py = col * self.tile_size, row * self.tile_size
                color_array[py:py+self.tile_size, px:px+self.tile_size] = color

        image = Image.fromarray(color_array, 'RGB')

        # Paste textures for non-water terrain
        for terrain_type, texture in self.textures.items():
            if terrain_type == TerrainType.WATER:
                continue  # water drawn via smooth mask below
            mask = (self.terrain_grid == terrain_type)
            rows, cols = np.where(mask)
            for row, col in zip(rows, cols):
                px, py = col * self.tile_size, row * self.tile_size
                texture_tile = self.draw_tile(None, px, py, colors[terrain_type], terrain_type, tile_x=col, tile_y=row)
                if texture_tile:
                    image.paste(texture_tile, (px, py))

        if TerrainType.GRASS in self.textures:
            water_mask = (self.terrain_grid == TerrainType.WATER)
            rows, cols = np.where(water_mask)
            for row, col in zip(rows, cols):
                px, py = col * self.tile_size, row * self.tile_size
                texture_tile = self.draw_tile(None, px, py, colors[TerrainType.GRASS], TerrainType.GRASS, tile_x=col, tile_y=row)
                if texture_tile:
                    image.paste(texture_tile, (px, py))

        image = self._render_smooth_water(image, colors)

        if show_grid:
            draw = ImageDraw.Draw(image)
            self.draw_grid(draw, img_width, img_height)

        # Foliage rendering
        if self.foliage_folder and os.path.isdir(self.foliage_folder) and self.foliage_tiles:
            target_size = self.tile_size

            # Pre-load and resize every asset, keyed by (subdir, filename)
            asset_cache = {}
            for subdir, files in self.foliage_assets.items():
                subdir_path = os.path.join(self.foliage_folder, subdir)
                for filename in files:
                    filepath = os.path.join(subdir_path, filename)
                    obj = Image.open(filepath).convert("RGBA")
                    aspect = obj.width / obj.height
                    if obj.width >= obj.height:
                        obj = obj.resize((target_size, max(1, int(target_size / aspect))), Image.LANCZOS)
                    else:
                        obj = obj.resize((max(1, int(target_size * aspect)), target_size), Image.LANCZOS)
                    asset_cache[(subdir, filename)] = obj

            image = image.convert("RGBA")

            for subdir, tiles in self.foliage_tiles.items():
                files = self.foliage_assets.get(subdir, [])
                if not files:
                    continue
                local_rng = random.Random(self.seed ^ hash(subdir) ^ 0xDEADBEEF)
                for row, col in tiles:
                    chosen_file = local_rng.choice(files)
                    obj = asset_cache[(subdir, chosen_file)]
                    x_offset = local_rng.random() - 0.5
                    y_offset = local_rng.random() - 0.5
                    px = int((col + x_offset) * self.tile_size) + (self.tile_size - obj.width) // 2
                    py = int((row + y_offset) * self.tile_size) + (self.tile_size - obj.height) // 2
                    image.paste(obj, (px, py), mask=obj)

            image = image.convert("RGB")

        # Re-stamp floor tiles over foliage so building interiors are never obscured
        if TerrainType.FLOOR in self.textures:
            floor_mask = (self.terrain_grid == TerrainType.FLOOR)
            rows, cols = np.where(floor_mask)
            for row, col in zip(rows, cols):
                px, py = col * self.tile_size, row * self.tile_size
                texture_tile = self.draw_tile(None, px, py, (180, 160, 130), TerrainType.FLOOR, tile_x=col, tile_y=row)
                if texture_tile:
                    image.paste(texture_tile, (px, py))
                else:
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([px, py, px + self.tile_size, py + self.tile_size], fill=(180, 160, 130))

        image = self._render_building_walls(image)

        return image

    def _render_building_walls(self, image: Image.Image) -> Image.Image:
        if not self.building or not self.building.wall_segments:
            return image

        ts = self.tile_size
        # Wall visually spans a full tile, centered on the grid line
        wall_thickness = ts
        fallback_px = max(6, ts // 10)  # only used when no asset is loaded

        wall_images: dict = {}
        if self.building_folder and os.path.isdir(self.building_folder):
            wall_files = sorted([
                f for f in os.listdir(self.building_folder)
                if f.lower().endswith('.png') and
                   os.path.isfile(os.path.join(self.building_folder, f)) and
                   'wall' in f.lower()
            ])
            if wall_files:
                raw = Image.open(
                    os.path.join(self.building_folder, wall_files[0])
                ).convert('RGBA')
                raw_w, raw_h = raw.size  # e.g. 3x2 tiles -> wider than tall

                # The asset has transparent padding so the visible wall only occupies
                # ~half the image width. Scale the long axis to 2.5*ts so the visible
                # portion fills one tile segment; thickness follows naturally.
                h_w = round(ts * 2.5)
                h_h = max(1, round(h_w * raw_h / raw_w))
                wall_h = raw.resize((h_w, h_h), Image.LANCZOS)

                # Vertical wall: rotate 90 degrees so the long axis becomes vertical,
                # then apply the same 2.5*ts scaling on the long axis.
                raw_rot = raw.rotate(90, expand=True)  # now taller than wide
                v_h = round(ts * 2.5)
                v_w = max(1, round(v_h * raw_rot.width / raw_rot.height))
                wall_v = raw_rot.resize((v_w, v_h), Image.LANCZOS)

                wall_images['H'] = wall_h
                wall_images['V'] = wall_v

        image = image.convert('RGBA')
        draw = ImageDraw.Draw(image)
        fallback_color = (60, 40, 20, 255)

        for seg in self.building.wall_segments:
            (gx0, gy0), (gx1, gy1) = seg
            px0, py0 = gx0 * ts, gy0 * ts
            px1, py1 = gx1 * ts, gy1 * ts

            # Horizontal wall: both grid points share the same grid-y
            is_horizontal = (gy0 == gy1)
            # Grid-line pixel coordinate (the border itself)
            line_x = min(px0, px1)
            line_y = min(py0, py1)

            if is_horizontal:
                # Center both axes on the grid line/segment midpoint
                if 'H' in wall_images:
                    wimg = wall_images['H']
                    seg_mid_x = line_x + ts // 2
                    paste_x = seg_mid_x - wimg.width // 2
                    paste_y = line_y - wimg.height // 2
                    image.paste(wimg, (paste_x, paste_y), mask=wimg)
                else:
                    half = fallback_px // 2
                    draw.rectangle(
                        [line_x, line_y - half, line_x + ts, line_y + half],
                        fill=fallback_color
                    )
            else:  # vertical wall
                # Center both axes on the grid line/segment midpoint
                if 'V' in wall_images:
                    wimg = wall_images['V']
                    seg_mid_y = line_y + ts // 2
                    paste_x = line_x - wimg.width // 2
                    paste_y = seg_mid_y - wimg.height // 2
                    image.paste(wimg, (paste_x, paste_y), mask=wimg)
                else:
                    half = fallback_px // 2
                    draw.rectangle(
                        [line_x - half, line_y, line_x + half, line_y + ts],
                        fill=fallback_color
                    )

        image = self._render_doors(image)

        image = image.convert('RGB')
        return image

    def _render_doors(self, image: Image.Image) -> Image.Image:
        if not self.building:
            return image

        all_doors = []
        if self.building.entrance:
            all_doors.append(self.building.entrance)
        all_doors.extend(self.building.doors)

        if not all_doors:
            return image

        ts = self.tile_size

        # Load door asset - look for files with 'door' in the name
        door_raw = None
        if self.building_folder and os.path.isdir(self.building_folder):
            door_files = sorted([
                f for f in os.listdir(self.building_folder)
                if f.lower().endswith('.png') and
                   os.path.isfile(os.path.join(self.building_folder, f)) and
                   'door' in f.lower()
            ])
            if door_files:
                door_raw = Image.open(
                    os.path.join(self.building_folder, door_files[0])
                ).convert('RGBA')

        if door_raw is None:
            return image

        raw_w, raw_h = door_raw.size
        long = max(raw_w, raw_h)
        short = min(raw_w, raw_h)
        scale_long = ts * 2
        scale_short = max(1, round(scale_long * short / long))

        if raw_w > raw_h:
            door_raw = door_raw.rotate(90, expand=True)

        door_h = door_raw.resize((scale_short, scale_long), Image.LANCZOS)
        door_v = door_raw.rotate(90, expand=True).resize((scale_long, scale_short), Image.LANCZOS)

        image = image.convert('RGBA')

        for (row, col, side) in all_doors:
            if side == 'N':
                line_x = col * ts + ts // 2
                line_y = row * ts
                dimg = door_h
            elif side == 'S':
                line_x = col * ts + ts // 2
                line_y = (row + 1) * ts
                dimg = door_h
            elif side == 'W':
                line_x = col * ts
                line_y = row * ts + ts // 2
                dimg = door_v
            else:  # 'E'
                line_x = (col + 1) * ts
                line_y = row * ts + ts // 2
                dimg = door_v

            paste_x = line_x - dimg.width // 2
            paste_y = line_y - dimg.height // 2
            image.paste(dimg, (paste_x, paste_y), mask=dimg)

        return image

    def _render_smooth_water(self, base_image, colors):
        if not hasattr(self, 'river_pixel_mask') or self.river_pixel_mask is None:
            return base_image

        ts = self.tile_size
        img_w = self.width * ts
        img_h = self.height * ts

        # Render shore layer beneath water
        shore_color = (238, 214, 175)
        if hasattr(self, 'river_spline_points') and hasattr(self, 'river_radius_px'):
            shore_radius_px = self.river_radius_px * 1.3  # * 1.0 = river size, want it wider than river
            shore_mask = self._rasterize_river_spline(
                self.river_spline_points, shore_radius_px, img_w, img_h
            )

            shore_layer = Image.new('RGB', (img_w, img_h))
            if TerrainType.SAND in self.textures:
                sand_tex = self.textures[TerrainType.SAND]
                for ty in range(0, img_h, sand_tex.height):
                    for tx in range(0, img_w, sand_tex.width):
                        shore_layer.paste(sand_tex, (tx, ty))
            else:
                shore_layer.paste(shore_color, [0, 0, img_w, img_h])

            shore_mask_img = Image.fromarray((shore_mask * 255).astype(np.uint8), 'L')
            result = base_image.copy()
            result.paste(shore_layer, (0, 0), mask=shore_mask_img)
            base_image = result

        water_layer = Image.new('RGB', (img_w, img_h))
        if TerrainType.WATER in self.textures:
            water_mask_tiles = (self.terrain_grid == TerrainType.WATER)
            wrows, wcols = np.where(water_mask_tiles)
            for row, col in zip(wrows, wcols):
                px, py = col * ts, row * ts
                tile = self.draw_tile(None, px, py, colors[TerrainType.WATER], TerrainType.WATER, tile_x=col, tile_y=row)
                if tile:
                    water_layer.paste(tile, (px, py))
                else:
                    draw = ImageDraw.Draw(water_layer)
                    draw.rectangle([px, py, px+ts, py+ts], fill=colors[TerrainType.WATER])
        else:
            # Flat color fallback
            wc = colors[TerrainType.WATER]
            draw = ImageDraw.Draw(water_layer)
            water_mask_tiles = (self.terrain_grid == TerrainType.WATER)
            wrows, wcols = np.where(water_mask_tiles)
            for row, col in zip(wrows, wcols):
                px, py = col * ts, row * ts
                draw.rectangle([px, py, px+ts, py+ts], fill=wc)

        # river_pixel_mask is a boolean array at pixel resolution (img_h x img_w)
        # Use as alpha channel to composite water over base
        mask_img = Image.fromarray((self.river_pixel_mask * 255).astype(np.uint8), 'L')

        result = base_image.copy()
        result.paste(water_layer, (0, 0), mask=mask_img)
        return result

    def draw_tile(self, draw, x, y, base_color, terrain_type=None, tile_x=0, tile_y=0):
        size = self.tile_size

        # If textures are loaded and this terrain type has a texture, use it
        if self.textures and terrain_type in self.textures:
            texture = self.textures[terrain_type]

            # Calculate position in the continuous texture
            texture_x = (tile_x * size) % texture.width
            texture_y = (tile_y * size) % texture.height
            texture_tile = Image.new('RGB', (size, size))
            width_available = min(size, texture.width - texture_x)
            height_available = min(size, texture.height - texture_y)

            main_section = texture.crop((
                texture_x, 
                texture_y, 
                texture_x + width_available, 
                texture_y + height_available
            ))
            texture_tile.paste(main_section, (0, 0))

            # wrap horizontally
            if width_available < size:
                right_section = texture.crop((
                    0, 
                    texture_y, 
                    size - width_available, 
                    texture_y + height_available
                ))
                texture_tile.paste(right_section, (width_available, 0))

            # wrap vertically
            if height_available < size:
                bottom_section = texture.crop((
                    texture_x, 
                    0, 
                    texture_x + width_available, 
                    size - height_available
                ))
                texture_tile.paste(bottom_section, (0, height_available))

            # wrap both
            if width_available < size and height_available < size:
                corner_section = texture.crop((
                    0, 
                    0, 
                    size - width_available, 
                    size - height_available
                ))
                texture_tile.paste(corner_section, (width_available, height_available))

            return texture_tile
        else:
            draw.rectangle([x, y, x + size, y + size], fill=(base_color))
            return None

    def draw_grid(self, draw, img_width, img_height):
        grid_color = (50, 50, 50, 128)

        # Vertical lines
        for x in range(0, img_width + 1, self.tile_size):
            draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)

        # Horizontal lines
        for y in range(0, img_height + 1, self.tile_size):
            draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)

    def generate_river(self, river_width):
        ts = self.tile_size
        img_w = self.width * ts
        img_h = self.height * ts

        choose_start_wall = random.randint(0, 3)  # 0=left, 1=top, 2=right, 3=bottom
        choose_end_wall = choose_start_wall
        while choose_end_wall == choose_start_wall:
            choose_end_wall = random.randint(0, 3)

        def wall_point_px(wall):
            if wall == 0:   # left
                return (0, random.randint(ts, img_h - ts))
            elif wall == 1: # top
                return (random.randint(ts, img_w - ts), 0)
            elif wall == 2: # right
                return (img_w, random.randint(ts, img_h - ts))
            else:           # bottom
                return (random.randint(ts, img_w - ts), img_h)

        start_px = wall_point_px(choose_start_wall)
        end_px   = wall_point_px(choose_end_wall)

        # Generate 2-3 river waypoints on map
        # Divide the map into segments, pick one point per segment
        # River flows naturally between points without looping back
        num_waypoints = random.randint(2, 3)
        interior_pts = []
        padding = ts * 2
        for i in range(num_waypoints):
            t = (i + 1) / (num_waypoints + 1)

            base_x = start_px[0] + (end_px[0] - start_px[0]) * t
            base_y = start_px[1] + (end_px[1] - start_px[1]) * t
            jitter_x = random.uniform(-img_w * 0.25, img_w * 0.25)
            jitter_y = random.uniform(-img_h * 0.25, img_h * 0.25)
            wx = int(max(padding, min(img_w - padding, base_x + jitter_x)))
            wy = int(max(padding, min(img_h - padding, base_y + jitter_y)))
            interior_pts.append((wx, wy))

        px_points = [start_px] + interior_pts + [end_px]

        river_radius_px = river_width * ts
        pixel_mask = self._rasterize_river_spline(px_points, river_radius_px, img_w, img_h)

        # store for shore rendering
        self.river_spline_points = px_points
        self.river_radius_px = river_radius_px

        tiles = set()
        mask_reshaped = pixel_mask.reshape(self.height, ts, self.width, ts)
        tile_covered = mask_reshaped.any(axis=(1, 3))
        rows, cols = np.where(tile_covered)
        for r, c in zip(rows, cols):
            tiles.add((c, r))

        return pixel_mask, tiles

    def _rasterize_river_spline(self, px_points, radius_px, img_w, img_h):
        if len(px_points) < 2:
            return np.zeros((img_h, img_w), dtype=bool)

        xs = np.array([p[0] for p in px_points], dtype=float)
        ys = np.array([p[1] for p in px_points], dtype=float)

        k = min(3, len(px_points) - 1)

        try:
            tck, u = splprep([xs, ys], s=len(px_points) * (radius_px ** 0.5), k=k)
            num_samples = max(200, len(px_points) * 8)
            u_new = np.linspace(0, 1, num_samples)
            smooth_x, smooth_y = splev(u_new, tck)
        except Exception:
            smooth_x, smooth_y = xs, ys

        mask_img = Image.new('L', (img_w, img_h), 0)
        draw = ImageDraw.Draw(mask_img)

        diameter = int(radius_px * 2)
        pts = list(zip(smooth_x.tolist(), smooth_y.tolist()))

        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            draw.line([(x0, y0), (x1, y1)], fill=255, width=diameter)

        r = int(radius_px)
        for x, y in pts[::max(1, len(pts) // 200)]:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=255)

        return np.array(mask_img) > 127

    def distance(self, p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def get_tiles_in_radius(self, target, r):
        tiles = set()
        for y in range(target[1] - int(r), target[1] + int(r) + 1):
            for x in range(target[0] - int(r), target[0] + int(r) + 1):
                if not (x < 0 or x >= self.width or y < 0 or y >= self.height or self.distance((x,y), (target[0],target[1])) > r):
                    tiles.add((x, y))
        return tiles