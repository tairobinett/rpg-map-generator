from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import terrain_generator as tg
from fastapi.responses import StreamingResponse
from io import BytesIO


app = FastAPI()

# Allow your React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def hello_world():
    return {"message": "Hello World!"}

@app.post("/generate_map")
def generate_map(seed):
    try:
        input_seed_int = int(seed)
        # print(f"input_seed_int value: {input_seed_int}")
    except ValueError:
        print("Invalid input.")
        exit()

    generator = tg.TerrainGenerator(width=30, height=30, seed=input_seed_int, tile_size=128)
    
    print("Generating terrain...")
    generator.generate_terrain(scale=0.1, octaves=4)
    
    print("Rendering image...")
    image = generator.render_to_image(show_grid=True)

    image_byte_array = BytesIO()
    image.save(image_byte_array, format="PNG")
    image_byte_array.seek(0)
    return StreamingResponse(image_byte_array, media_type="image/png")
    
    # output_file = "battlemap_test.png"
    # image.save(output_file)
    # print(f"Map saved to {output_file}")
