import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './assets/tailwindcss.css';
import Layout from './components/Layout';
import Home from './views/Home';  
import EnterTeam from './views/EnterTeam';
function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}> 
          <Route path="/" element={<Home />} />
          <Route path="/enter-team" element={<EnterTeam />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App;
