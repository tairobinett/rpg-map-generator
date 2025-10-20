import numpy as np
from PIL import Image, ImageDraw
from opensimplex import OpenSimplex
import random


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

