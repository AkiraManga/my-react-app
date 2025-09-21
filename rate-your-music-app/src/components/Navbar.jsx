import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Navbar.css";

function Navbar() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    try {
      const configResp = await fetch("/config.json");
      const config = await configResp.json();

      // Caso 1: album_id tipo "a001"
      if (/^a\d+$/i.test(trimmed)) {
        navigate(`/album/${trimmed.toLowerCase()}`);
      } else {
        // Caso 2: ricerca per titolo
        const resp = await fetch(
          `${config.apiBaseUrl}albums/by-title/${encodeURIComponent(trimmed)}`
        );

        if (resp.ok) {
          const data = await resp.json();
          if (data.length === 1) {
            // Album unico trovato → redirect diretto
            navigate(`/album/${data[0].album_id}`);
          } else {
            // Nessun risultato o più risultati → pagina di ricerca
            navigate(`/search/${encodeURIComponent(trimmed)}`);
          }
        } else {
          // fallback
          navigate(`/search/${encodeURIComponent(trimmed)}`);
        }
      }
    } catch (err) {
      console.error("Errore ricerca:", err);
      navigate(`/search/${encodeURIComponent(trimmed)}`);
    }

    setQuery("");
  };

  return (
    <nav className="navbar">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Cerca album per titolo, artista o codice..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </form>
    </nav>
  );
}

export default Navbar;
