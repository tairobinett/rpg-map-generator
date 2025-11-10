import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState("test")
  const [imageURL, setImageURL] = useState("")
  const [seed, setSeed] = useState("")

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

  const generateImage = async () => {
    try{
      console.log(seed)
      const response = await fetch('http://127.0.0.1:8000/generate_map', {
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify({
          seed:seed
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
        <button onClick={() => generateImage()}>
          Generate map
        </button>
      </div>

      <div className="card">
        {
          imageURL && <img src={imageURL} alt="Terrain map" style={{ maxWidth: '800px', width: '100%', height: 'auto', marginTop: '1rem' }} />
          
        }
      </div>
    </>
  )
}

export default App
