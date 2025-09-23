import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./styles/Navbar.css";

export default function Navbar() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (query.startsWith("a")) {
      // cerca per ID album
      navigate(`/album/${query}`);
    } else {
      // cerca per titolo
      navigate(`/search/${query}`);
    }

    setQuery("");
  };

  return (
    <nav className="navbar">
      {/* Sinistra */}
      <div className="left-container">
        <Link to="/" className="nav-btn">Home</Link>
      </div>

      {/* Centro: barra di ricerca */}
      <div className="center-container">
        <form onSubmit={handleSubmit} style={{ width: "100%" }}>
          <input
            type="text"
            placeholder="Cerca album..."
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
      </div>

      {/* Destra */}
      <div className="right-container">
        <Link to="/profile" className="nav-btn">Profilo</Link>
        <button className="nav-btn">Login</button>
      </div>
    </nav>
  );
}
