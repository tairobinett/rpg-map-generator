import terrain_generator as tg

if __name__ == "__main__":
    generator = tg.TerrainGenerator(width=30, height=30, seed=11112, tile_size=128)
    
    print("Generating terrain...")
    generator.generate_terrain(scale=0.1, octaves=4)
    
    print("Rendering image...")
    image = generator.render_to_image(show_grid=True)
    
    output_file = "battlemap_test.png"
    image.save(output_file)
    print(f"Map saved to {output_file}")
