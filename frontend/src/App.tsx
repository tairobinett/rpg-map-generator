import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState("test")
  const [imageURL, setImageURL] = useState("")

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
      const response = await fetch('http://127.0.0.1:8000/generate_map', {
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify({
          seed:"1"
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
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => generateImage()}>
          count is {count}
        </button>
        {
          imageURL && <img src={imageURL} alt="Terrain map" />
          
        }
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
