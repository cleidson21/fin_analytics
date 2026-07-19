import { useState } from 'react'

function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [jsonResponse, setJsonResponse] = useState('Nenhuma resposta ainda...')

  const handleLogin = async () => {
    setJsonResponse('Iniciando login... (simulado, ainda sem integração)')
    // Futura integração de login aqui
  }

  const handleTestUsersMe = async () => {
    setJsonResponse('Testando /users/me... (simulado, ainda sem integração)')
    // Futura integração /users/me aqui
  }

  return (
    <div>
      <h1>Playground de Desenvolvimento - FIN Analytics</h1>
      
      <div>
        <label>Email: </label>
        <input 
          type="email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
        />
      </div>

      <div>
        <label>Senha: </label>
        <input 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
        />
      </div>

      <div>
        <button onClick={handleLogin}>LOGIN</button>
        <button onClick={handleTestUsersMe}>TESTAR /users/me</button>
      </div>

      <div>
        <h2>Response JSON</h2>
        <pre>{jsonResponse}</pre>
      </div>
    </div>
  )
}

export default App
