import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 Bienvenido a Lunt</h1>
        <p>Proyecto configurado y listo para desarrollo</p>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            Contador: {count}
          </button>
        </div>
        <p className="info">
          Edita <code>src/App.jsx</code> y guarda para ver los cambios en tiempo real
        </p>
      </header>
    </div>
  )
}

export default App
