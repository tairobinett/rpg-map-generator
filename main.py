import terrain_generator as tg

if __name__ == "__main__":
    input_seed = input("Enter world seed (integer only): ")
    try:
        input_seed_int = int(input_seed)
        # print(f"input_seed_int value: {input_seed_int}")
    except ValueError:
        print("Invalid input.")
        exit()

    generator = tg.TerrainGenerator(width=30, height=30, seed=input_seed_int, tile_size=128)
    
    print("Generating terrain...")
    generator.generate_terrain(scale=0.1, octaves=4)
    
    print("Rendering image...")
    image = generator.render_to_image(show_grid=True)
    
    output_file = "battlemap_test.png"
    image.save(output_file)
    print(f"Map saved to {output_file}")
