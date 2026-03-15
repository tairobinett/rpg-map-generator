import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Slider from '@mui/material/Slider'

function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState("test")
  const [imageURL, setImageURL] = useState("")
  const [seed, setSeed] = useState("")
  const [height, setHeight] = useState("15")
  const [width, setWidth] = useState("15")
  const [river_width, setRiverWidth] = useState("1")
  const [road_width, setRoadWidth] = useState("1")
  const [flower_density, setFlowerDensity] = useState(50)
  const [rock_density, setRockDensity] = useState(50)
  const [bush_density, setBushDensity] = useState(50)
  const [flower_coverage, setFlowerCoverage] = useState(50)
  const [rock_coverage, setRockCoverage] = useState(50)
  const [bush_coverage, setBushCoverage] = useState(50)
  const [grid_toggle, setGridToggle] = useState(true)

  const handleClick = async () => {
    try{
      const response = await fetch('http://127.0.0.1:8000/hello');
      const data = await response.json();
      setMessage(data.message);
    }
    catch(e){
      console.error("Error: ", e);
    }
  }

  const handleSliderChangeFlowerD = (event: Event, newFlowerDensity: number) => {
    setFlowerDensity(newFlowerDensity);
  };

  const handleSliderChangeRockD = (event: Event, newRockDensity: number) => {
    setRockDensity(newRockDensity);
  };

  const handleSliderChangeBushD = (event: Event, newBushDensity: number) => {
    setBushDensity(newBushDensity);
  };
  const handleSliderChangeFlowerC = (event: Event, newFlowerCoverage: number) => {
    setFlowerCoverage(newFlowerCoverage);
  };

  const handleSliderChangeRockC = (event: Event, newRockCoverage: number) => {
    setRockCoverage(newRockCoverage);
  };

  const handleSliderChangeBushC = (event: Event, newBushCoverage: number) => {
    setBushCoverage(newBushCoverage);
  };

  const generateImage = async () => {
    try{
      console.log(seed)
      const response = await fetch('http://127.0.0.1:8000/generate_map', { // http://34.23.208.207:5173/ for remote hosting
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify({
          seed:seed,
          height:height,
          width:width,
          river_width:river_width,
          road_width:road_width,
          flower_density:flower_density,
          rock_density:rock_density,
          bush_density:bush_density,
          flower_coverage:flower_coverage,
          rock_coverage:rock_coverage,
          bush_coverage:bush_coverage,
          grid:grid_toggle
        }),
      });
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setImageURL(url);
    }
    catch(e){
      console.error("Error: ", e);
    }
  }

  return (
    <>
      <h1>RPG Map Generator</h1>

      <div>
        <label>
          Enter seed: <input 
            name="seedInput" 
            value={seed}
            onChange={e => setSeed(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          Enter map width: <input 
            value={width}
            onChange={e => setWidth(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          Enter map height: <input 
            value={height}
            onChange={e => setHeight(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          Enter river width: <input 
            value={river_width}
            onChange={e => setRiverWidth(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          Enter road width: <input 
            value={road_width}
            onChange={e => setRoadWidth(e.target.value)}
          />
        </label>
      </div>

      <div>
        <label>
          Flower density percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeFlowerD}
          />
        </label>
      </div>
      <div>
        <label>
          Flower coverage percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeFlowerC}
          />
        </label>
      </div>

      <div>
        <label>
          Rock density percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeRockD}
          />
        </label>
      </div>
      <div>
        <label>
          Rock coverage percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeRockC}
          />
        </label>
      </div>

      <div>
        <label>
          Bush density percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeBushD}
          />
        </label>
      </div>
      <div>
        <label>
          Bush coverage percentage: 
          <Slider
            size="small"
            defaultValue={50}
            aria-label="Small"
            valueLabelDisplay="auto"
            onChange={handleSliderChangeBushC}
          />
        </label>
      </div>

      
      <div>
        <label>
          Toggle grid<input 
            type="checkbox"
            checked={grid_toggle}
            onChange={() => setGridToggle(!grid_toggle)}
          />
        </label>
      </div>
      <div>
        <button onClick={() => generateImage()}>
          Generate map
        </button>
      </div>
      <div className="card">
        {
          imageURL && <img src={imageURL} alt="Terrain map" style={{ maxWidth: '800px', width: '100%', height: 'auto', marginTop: '1rem' }} />
          
        }
      </div>

      <p>
        Tile textures by 
        <a href="https://2minutetabletop.com"> 2 Minute Tabletop</a>, 
        licensed under 
        <a href="https://creativecommons.org/licenses/by-nc/4.0/"> CC BY-NC 4.0</a>
      </p>
    </>
  )
}

export default App
