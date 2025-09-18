import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from './components/Header';
import Gallery3D from './components/Gallery3D';
import Callback from './Callback';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Routes>
          <Route path="/" element={<Gallery3D />} />
          <Route path="/callback" element={<Callback />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
