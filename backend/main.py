from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import terrain_generator as tg
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
import hashlib


app = FastAPI()

# Allow your React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class seed_request(BaseModel): 
    seed:str
    height:int
    width:int
    river_width:int
    flower_density:float
    rock_density:float
    bush_density:float
    flower_coverage:float
    rock_coverage:float
    bush_coverage:float
    grid:bool

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
        input_flower_density_float = float(request.flower_density) / 100
        input_rock_density_float = float(request.rock_density) / 100
        input_bush_density_float = float(request.bush_density) / 100
        input_flower_coverage_float = 1.0 - float(request.flower_coverage) / 100 # generate_terrain checks above threshold
        input_rock_coverage_float = 1.0 - float(request.rock_coverage) / 100
        input_bush_coverage_float = 1.0 - float(request.bush_coverage) / 100
        input_grid_toggle = bool(request.grid)
        print(f"input_river_width_int value: {input_river_width_int}")
        # print(f"input_seed_int value: {input_seed_int}")
    except ValueError:
        print("Invalid input.")
        exit()

    input_seed_int = int(hashlib.md5(input_seed.encode()).hexdigest(), 16) % 2**32

    generator = tg.TerrainGenerator(width=input_width_int, height=input_height_int, seed=input_seed_int, tile_size=128, texture_folder='textures', asset_folder='assets')
    
    print("Generating terrain...")
    foliage_density = [input_flower_density_float, input_rock_density_float, input_bush_density_float]
    foliage_coverage = [input_flower_coverage_float, input_rock_coverage_float, input_bush_coverage_float]
    generator.generate_terrain(river_width=input_river_width_int, foliage_density=foliage_density, foliage_coverage=foliage_coverage, scale=0.1, octaves=4)
    
    print("Rendering image...")
    image = generator.render_to_image(show_grid=input_grid_toggle)

    image_byte_array = BytesIO()
    image.save(image_byte_array, format="PNG")
    image_byte_array.seek(0)
    return StreamingResponse(image_byte_array, media_type="image/png")
    
    # output_file = "battlemap_test.png"
    # image.save(output_file)
    # print(f"Map saved to {output_file}")