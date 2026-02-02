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
    def __init__(self, width, height, seed, tile_size=128):
        self.width = width
        self.height = height
        self.seed = seed
        self.tile_size = tile_size
        
        random.seed(seed)
        np.random.seed(seed)
        self.noise = OpenSimplex(seed)
        
        self.terrain_grid = np.zeros((height, width), dtype=int)
        
    def generate_terrain(self, scale=0.1, octaves=4):
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
        self.terrain_grid = self.noise_to_terrain(noise_map)
        
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
                terrain_type = self.terrain_grid[y, x]
                color = colors[terrain_type]
                
                # Calculate pixel coordinates
                px = x * self.tile_size
                py = y * self.tile_size
                
                self.draw_tile(draw, px, py, color)
        
        if show_grid:
            self.draw_grid(draw, img_width, img_height)
        
        return image
    
    def draw_tile(self, draw, x, y, base_color):
        size = self.tile_size
        draw.rectangle([x, y, x + size, y + size], fill=base_color)
    
    def draw_grid(self, draw, img_width, img_height):
        grid_color = (50, 50, 50, 128)
        
        # Vertical lines
        for x in range(0, img_width + 1, self.tile_size):
            draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)
        
        # Horizontal lines
        for y in range(0, img_height + 1, self.tile_size):
            draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)


    def generate_terrain_grass(self, scale=0.1, octaves=4):
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
        
        return self.terrain_grid

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
    
    def generate_terrain_river(self, river_width, scale=0.1, octaves=4,):
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

        return self.terrain_grid