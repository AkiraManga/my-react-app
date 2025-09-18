import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from './components/Header';
import Gallery3D from './components/Gallery3D';
import Callback from './Callback';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Gallery3D />   {/* <-- sempre visibile */}
        <Routes>
          <Route path="/" element={null} />
          <Route path="/callback" element={<Callback />} />
        </Routes>
      </div>
    </Router>
  );
}


export default App;
