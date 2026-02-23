import numpy as np
from PIL import Image, ImageDraw
from opensimplex import OpenSimplex
import random
import math


class TerrainType:
    WATER = 0
    SAND = 1
    GRASS = 2
    FOREST = 3
    HILL = 4
    MOUNTAIN = 5


class TerrainGenerator:
    def __init__(self, width, height, seed, tile_size=128, texture_folder=None, asset_folder=None):
        self.width = width
        self.height = height
        self.seed = seed
        self.tile_size = tile_size
        self.texture_folder = texture_folder
        self.asset_folder = asset_folder
        self.foliage_tiles = []
        
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
        
        foliage_texture_files = {
            "bush":'bush1.png'
        }

        for terrain_type, filename in foliage_texture_files.items():
            filepath = os.path.join(self.asset_folder, filename)
            if os.path.exists(filepath):
                texture = Image.open(filepath).convert('RGB')
                self.textures[terrain_type] = texture
            else:
                print(f"Warning: Asset not found: {filepath}")
    

    def generate_terrain(self, river_width, scale=0.1, octaves=4, foliage_coverage=0.75):
        # Generate multi-octave noise
        noise_map = np.zeros((self.height, self.width))
        
        for octave in range(octaves):
            frequency = 2 ** octave
            amplitude = 1 / (2 ** octave)
            
            for y in range(self.height):
                for x in range(self.width):
                    noise_val = self.noise.noise2(
                        x * scale * frequency,
                        y * scale * frequency
                    )
                    noise_map[y, x] += noise_val * amplitude
        
        # Normalize to 0-1 range
        noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
        
        # Convert noise values to terrain types using thresholds
        self.terrain_grid.fill(TerrainType.GRASS)

        river_tiles = self.generate_river(river_width)
        
        for tile in list(river_tiles):
            self.terrain_grid[tile[0], tile[1]] = TerrainType.WATER
        
        # Get tiles to place foliage
        threshold_tiles = self.get_tiles_above_threshold(noise_map, 0.5)

        # Get set of grass tiles
        threshold_grass_tiles = set()
        random.seed(self.seed)
        for tile in threshold_tiles:
            row, column = int(tile[0]), int(tile[1])
            if self.terrain_grid[row, column] == TerrainType.GRASS and random.random() <= foliage_coverage:
                    threshold_grass_tiles.add((row, column))
        
        self.foliage_tiles = threshold_grass_tiles

        return self.terrain_grid
    
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
        
        image = Image.new('RGB', (img_width, img_height))
        draw = ImageDraw.Draw(image)
        
        colors = {
            TerrainType.WATER:      (65, 105, 225),
            TerrainType.SAND:       (238, 214, 175),
            TerrainType.GRASS:      (107, 142, 35),
            TerrainType.FOREST:     (34, 139, 34),
            TerrainType.HILL:       (139, 90, 43),
            TerrainType.MOUNTAIN:   (105, 105, 105),
        }
        
        for y in range(self.height):
            for x in range(self.width):
                terrain_type = self.terrain_grid[x, y]
                color = colors[terrain_type]
                
                # Calculate pixel coordinates
                px = x * self.tile_size
                py = y * self.tile_size
                
                # Try to draw with texture, pass tile coordinates for continuous mapping
                texture_tile = self.draw_tile(draw, px, py, color, terrain_type, tile_x=x, tile_y=y)
                if texture_tile:
                    image.paste(texture_tile, (px, py))
        
        if show_grid:
            self.draw_grid(draw, img_width, img_height)
        
        #image = self.draw_object(image, 1.5, 2.3, 1.0, "assets/bush1.png")
        random.seed(self.seed)
        for row, column in self.foliage_tiles:
            x_offset = random.random() - 0.5
            y_offset = random.random() - 0.5
            image = self.draw_object(image, row + x_offset, column + y_offset, 1.0, "assets/bush1.png")

        return image
    
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
    
    def draw_object(self, image, x, y, scale, filepath):
        obj = Image.open(filepath).convert("RGBA")
        target_size = int(self.tile_size * scale)
        aspect = obj.width / obj.height
        
        if obj.width >= obj.height:
            obj = obj.resize((target_size, max(1, int(target_size / aspect))), Image.LANCZOS)
        else:
            obj = obj.resize((max(1, int(target_size * aspect)), target_size), Image.LANCZOS)
        

        px = int(x * self.tile_size) + (self.tile_size - obj.width) // 2
        py = int(y * self.tile_size) + (self.tile_size - obj.height) // 2

        image = image.convert("RGBA")
        image.paste(obj, (px, py), mask=obj)

        return image.convert("RGB")    
    
    def draw_grid(self, draw, img_width, img_height):
        grid_color = (50, 50, 50, 128)
        
        # Vertical lines
        for x in range(0, img_width + 1, self.tile_size):
            draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)
        
        # Horizontal lines
        for y in range(0, img_height + 1, self.tile_size):
            draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)

    def generate_river(self, river_width):

        choose_start_wall = random.randint(0,3) # 0=left, 1=top, 2=right, 3=bottom
        choose_end_wall = choose_start_wall
        while choose_end_wall == choose_start_wall:
            choose_end_wall = random.randint(0,3)

        river_start = (0,0)
        river_end = (0,0)
        mid_point = (random.randint(1,self.width-1), random.randint(1,self.height-1)) # Random point in interior
        target_weight = 0.75
        
        # Choose starting and ending points
        if choose_start_wall == 0:
            river_start = (0, random.randint(1, self.height-1))
        elif choose_start_wall == 1:
            river_start = (random.randint(1, self.width-1), 0)
        elif choose_start_wall == 2:
            river_start = (self.width-1, random.randint(1, self.height-1))
        else:
            river_start = (random.randint(1, self.width-1), self.height-1)

        if choose_end_wall == 0:
            river_end = (0, random.randint(1, self.height-1))
        elif choose_end_wall == 1:
            river_end = (0, random.randint(1, self.width-1))
        elif choose_end_wall == 2:
            river_end = (self.width-1, random.randint(1, self.height-1))
        else:
            river_end = (random.randint(1, self.width-1), self.height-1)
        
        tiles = set()
        counter = 0
        iteration_limit = 1000
        current_pos = river_start

        # River start to midpoint
        if(current_pos not in tiles and current_pos[0] >= 0 and current_pos[0] < self.width and current_pos[1] >= 0 and current_pos[1] < self.height):
            tiles.add(current_pos)
        while(not (current_pos[0] is mid_point[0] and current_pos[1] is mid_point[1]) and counter < iteration_limit):
            counter += 1
            if(current_pos not in tiles and current_pos[0] >= 0 and current_pos[0] < self.width and current_pos[1] >= 0 and current_pos[1] < self.height):
                tiles.add(current_pos)
            if(random.uniform(0, 1) < target_weight):
                if current_pos[0] < mid_point[0] and current_pos[1] < mid_point[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]+1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]+1)
                elif current_pos[0] < mid_point[0] and current_pos[1] > mid_point[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]+1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]-1)
                elif current_pos[0] > mid_point[0] and current_pos[1] < mid_point[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]-1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]+1)
                elif current_pos[0] > mid_point[0] and current_pos[1] > mid_point[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]-1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]-1)
                elif current_pos[0] < mid_point[0]:
                    current_pos = (current_pos[0]+1, current_pos[1]) # right
                elif current_pos[1] < mid_point[1]:
                    current_pos = (current_pos[0], current_pos[1]+1) # down
                elif current_pos[0] > mid_point[0]:
                    current_pos = (current_pos[0]-1, current_pos[1]) # left
                elif current_pos[1] > mid_point[1]:
                    current_pos = (current_pos[0], current_pos[1]-1) # up
            else:
                dir = random.randint(0, 3)
                if dir == 0:
                    if current_pos[0] - 1 > 0:
                        current_pos = (current_pos[0] - 1, current_pos[1])
                elif dir == 1:
                    if current_pos[1] - 1 > 0:
                        current_pos = (current_pos[0], current_pos[1] - 1)
                elif dir == 2:
                    if current_pos[0] + 1 < self.width - 1:
                        current_pos = (current_pos[0] + 1, current_pos[1])
                else:
                    if current_pos[1] - 1 < self.height - 1:
                        current_pos = (current_pos[0], current_pos[1] + 1)
        
        counter = 0
        # River midpoint to end
        while(current_pos[0] > 0 and current_pos[0] < self.width and current_pos[1] > 0 and current_pos[1] < self.height and 
                not (current_pos[0] is river_end[0] and current_pos[1] is river_end[1]) and counter < iteration_limit):
            counter += 1
            if(current_pos not in tiles and current_pos[0] >= 0 and current_pos[0] < self.width and current_pos[1] >= 0 and current_pos[1] < self.height):
                tiles.add(current_pos)
            if(random.uniform(0, 1) < target_weight):
                if current_pos[0] < river_end[0] and current_pos[1] < river_end[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]+1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]+1)
                elif current_pos[0] < river_end[0] and current_pos[1] > river_end[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]+1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]-1)
                elif current_pos[0] > river_end[0] and current_pos[1] < river_end[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]-1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]+1)
                elif current_pos[0] > river_end[0] and current_pos[1] > river_end[1]:
                    if(random.uniform(0, 1) < 0.5):
                        current_pos = (current_pos[0]-1, current_pos[1])
                    else:
                        current_pos = (current_pos[0], current_pos[1]-1)
                elif current_pos[0] < river_end[0]:
                    current_pos = (current_pos[0]+1, current_pos[1]) # right
                elif current_pos[1] < river_end[1]:
                    current_pos = (current_pos[0], current_pos[1]+1) # down
                elif current_pos[0] > river_end[0]:
                    current_pos = (current_pos[0]-1, current_pos[1]) # left
                elif current_pos[1] > river_end[1]:
                    current_pos = (current_pos[0], current_pos[1]-1) # up
            else:
                dir = random.randint(0, 3)
                if dir == 0:
                    if current_pos[0] - 1 > 0:
                        current_pos = (current_pos[0] - 1, current_pos[1])
                elif dir == 1:
                    if current_pos[1] - 1 > 0:
                        current_pos = (current_pos[0], current_pos[1] - 1)
                elif dir == 2:
                    if current_pos[0] + 1 < self.width - 1:
                        current_pos = (current_pos[0] + 1, current_pos[1])
                else:
                    if current_pos[1] - 1 < self.height - 1:
                        current_pos = (current_pos[0], current_pos[1] + 1)

        # Fill in final river tile
        if(current_pos not in tiles and current_pos[0] >= 0 and current_pos[0] < self.width and current_pos[1] >= 0 and current_pos[1] < self.height):
            tiles.add(current_pos)

        tiles_to_add = set()
        for tile in list(tiles):
            for t in self.get_tiles_in_radius(tile, river_width):
                tiles_to_add.add(t)
        tiles = tiles.union(tiles_to_add)

        return tiles
    
    def distance(self, p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def get_tiles_in_radius(self, target, r):
        tiles = set()
        for y in range(target[1] - int(r), target[1] + int(r) + 1):
            for x in range(target[0] - int(r), target[0] + int(r) + 1):
                if not (x < 0 or x >= self.width or y < 0 or y >= self.height or self.distance((x,y), (target[0],target[1])) > r):
                    tiles.add((x, y))
        return tiles
