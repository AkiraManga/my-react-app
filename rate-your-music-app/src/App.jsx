import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Gallery3D from "./components/Gallery3D";
import Callback from "./Callback";
import AlbumPage from "./components/AlbumPage";
import SearchResults from "./components/SearchResults"; // <-- nuovo import
import Profile from "./components/Profile";

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Routes>
          <Route path="/" element={<Gallery3D />} /> {/* Home */}
          <Route path="/callback" element={<Callback />} />
          <Route path="/album/:id" element={<AlbumPage />} /> {/* Pagina album */}
          <Route path="/search/:query" element={<SearchResults />} /> {/* Nuova pagina ricerca */}
          <Route path="/profile" element={<Profile />} />

        </Routes>
      </div>
    </Router>
  );
}

export default App;
