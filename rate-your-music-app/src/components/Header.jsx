import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from "react-router-dom";   // 👈 aggiunto Link
import '../styles/Header.css';

const Header = () => {
  const [config, setConfig] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  // Carica config.json al montaggio
  useEffect(() => {
    fetch("/config.json")
      .then(res => res.json())
      .then(data => {
        console.log("✅ Config caricata:", data);
        setConfig(data);
      })
      .catch(err => console.error("❌ Errore caricando config.json:", err));
  }, []);

  // Stato login (usa localStorage)
  useEffect(() => {
    const token = localStorage.getItem("id_token");
    setIsLoggedIn(!!token);

    const handleStorageChange = () => {
      const newToken = localStorage.getItem("id_token");
      setIsLoggedIn(!!newToken);
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  if (!config) {
    return <div>Caricamento...</div>; // Evita errori prima che config arrivi
  }

  const { clientId, cognitoDomain, redirectUri, logoutRedirect } = config;
  const scope = "email+openid+profile";
  const responseType = "code";

  const handleLogin = () => {
    const loginUrl =
      `https://${cognitoDomain}/login?client_id=${clientId}` +
      `&response_type=${responseType}` +
      `&scope=${scope}` + 
      `&redirect_uri=${encodeURIComponent(redirectUri)}`;

    console.log("🔗 Login URL generato:", loginUrl);
    window.location.href = loginUrl;
  };

  const handleLogout = () => {
    localStorage.removeItem("id_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    const logoutUrl =
      `https://${cognitoDomain}/logout?client_id=${clientId}` +
      `&logout_uri=${encodeURIComponent(logoutRedirect)}`;

    console.log("🔗 Logout URL generato:", logoutUrl);
    window.location.href = logoutUrl;
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) {
      const id = search.toLowerCase().replace(/\s+/g, "-");
      navigate(`/album/${id}`);
      setSearch("");
    }
  };

  return (
    <header className="main-header">
      {/* 👇 Link a sinistra */}
      <nav className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/profile">Profilo</Link>
      </nav>

      {/* 👇 Barra di ricerca al centro */}
      <div className="search-container">
        <form onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Cerca album..."
            className="search-bar"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>
      </div>

      {/* 👇 Login/Logout a destra */}
      <div className="login-container">
        {!isLoggedIn ? (
          <button type="button" className="login-button" onClick={handleLogin}>
            Login
          </button>
        ) : (
          <button type="button" className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
