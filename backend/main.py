from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import terrain_generator as tg
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
import hashlib
from typing import Literal


app = FastAPI()

# Allow your React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class seed_request(BaseModel): 
    seed:str
    height:int
    width:int
    river_width:int
    road_width:int
    flower_coverage:float
    rock_coverage:float
    bush_coverage:float
    grid:bool
    river_enabled:bool = True
    building_enabled:bool = True
    road_enabled:bool = True
    biome: Literal["grassland", "snow", "desert"] = "grassland"

@app.get("/hello")
def hello_world():
    return {"message": "Hello World!"}
 
@app.post("/generate_map")
def generate_map(request:seed_request):
    try:
        input_seed = str(request.seed)
        input_height_int = int(request.height)
        input_width_int = int(request.width)
        input_river_width_int = int(request.river_width)
        input_road_width_int = int(request.road_width)
        input_flower_coverage_float = 1.0 - float(request.flower_coverage) / 100 # generate_terrain checks above threshold
        input_rock_coverage_float = 1.0 - float(request.rock_coverage) / 100
        input_bush_coverage_float = 1.0 - float(request.bush_coverage) / 100
        input_grid_toggle = bool(request.grid)
        input_river_enabled = bool(request.river_enabled)
        input_building_enabled = bool(request.building_enabled)
        input_road_enabled = bool(request.road_enabled)
        input_biome = str(request.biome)
        print(f"input_river_width_int value: {input_river_width_int}")
        print(f"biome: {input_biome}")
    except ValueError:
        print("Invalid input.")
        exit()

    input_seed_int = int(hashlib.md5(input_seed.encode()).hexdigest(), 16) % 2**32

    # Select asset folders based on biome
    if input_biome == "snow":
        texture_folder = 'assets/ground_textures_snow'
        foliage_folder = 'assets/foliage_and_objects_snow'
    elif input_biome == "desert":
        texture_folder = 'assets/ground_textures_desert'
        foliage_folder = 'assets/foliage_and_objects_desert'
    else:
        texture_folder = 'assets/ground_textures'
        foliage_folder = 'assets/foliage_and_objects'

    generator = tg.TerrainGenerator(
        width=input_width_int,
        height=input_height_int,
        seed=input_seed_int,
        tile_size=128,
        texture_folder=texture_folder,
        foliage_folder=foliage_folder,
        building_folder='assets/buildings',
        biome=input_biome,
    )
    
    print("Generating terrain...")
    foliage_coverage = [input_flower_coverage_float, input_rock_coverage_float, input_bush_coverage_float]
    generator.generate_terrain(
        river_width=input_river_width_int,
        road_width=input_road_width_int,
        foliage_coverage=foliage_coverage,
        scale=0.1,
        octaves=4,
        river_enabled=input_river_enabled,
        building_enabled=input_building_enabled,
        road_enabled=input_road_enabled,
    )
    
    print("Rendering image...")
    image = generator.render_to_image(show_grid=input_grid_toggle)

    image_byte_array = BytesIO()
    image.save(image_byte_array, format="PNG")
    image_byte_array.seek(0)
    return StreamingResponse(image_byte_array, media_type="image/png")
