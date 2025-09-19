import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from './components/Header';
import Gallery3D from './components/Gallery3D';
import Callback from './Callback';
import AlbumPage from './components/AlbumPage';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Routes>
          <Route path="/" element={<Gallery3D />} />   {/* <-- Solo in home */}
          <Route path="/callback" element={<Callback />} />
          <Route path="/album/:id" element={<AlbumPage />} /> {/* <-- Pagina dedicata */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
