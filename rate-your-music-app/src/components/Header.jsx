import React, { useEffect, useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import "../styles/Header.css";

const Header = () => {
  const [config, setConfig] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  // ➜ carico il font "Material Symbols" direttamente qui (niente index.html)
  useEffect(() => {
    const LINK_ID = "material-symbols-outlined-link";
    if (!document.getElementById(LINK_ID)) {
      const link = document.createElement("link");
      link.id = LINK_ID;
      link.rel = "stylesheet";
      link.href =
        "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap";
      document.head.appendChild(link);
    }

    // un piccolo style per la resa delle icone (se non vuoi toccare i CSS)
    const STYLE_ID = "material-symbols-inline-style";
    if (!document.getElementById(STYLE_ID)) {
      const style = document.createElement("style");
      style.id = STYLE_ID;
      style.textContent = `
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 0, 'wght' 450, 'GRAD' 0, 'opsz' 24;
          font-size: 22px;
          line-height: 1;
          vertical-align: middle;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  // Carica config.json
  useEffect(() => {
    fetch("/config.json")
      .then((res) => res.json())
      .then((data) => setConfig(data))
      .catch(() => setConfig(null));
  }, []);

  // Controlla token in localStorage
  useEffect(() => {
    const checkToken = () => setIsLoggedIn(!!localStorage.getItem("id_token"));
    checkToken();
    const onStorage = () => checkToken();
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const slugify = (s) =>
    s
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-");

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) {
      navigate(`/album/${slugify(search)}`);
      setSearch("");
    }
  };

  const handleLogin = () => {
    if (!config) return;
    const { clientId, cognitoDomain, redirectUri } = config;
    const scope = "email+openid+profile";
    const responseType = "code";
    const loginUrl =
      `https://${cognitoDomain}/login?client_id=${clientId}` +
      `&response_type=${responseType}&scope=${scope}` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}`;
    window.location.href = loginUrl;
  };

  const handleLogout = () => {
    if (!config) return;
    localStorage.removeItem("id_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    const { clientId, cognitoDomain, logoutRedirect } = config;
    const logoutUrl =
      `https://${cognitoDomain}/logout?client_id=${clientId}` +
      `&logout_uri=${encodeURIComponent(logoutRedirect)}`;
    window.location.href = logoutUrl;
  };

  return (
    <header className="main-header">
      {/* SINISTRA: Home + Classifica (niente profilo) */}
      <nav className="nav-links">
        <NavLink to="/" end className="nav-link">
          <span className="material-symbols-outlined">home</span>
          <span className="nav-label">Home</span>
        </NavLink>
        <NavLink to="/charts" className="nav-link">
          <span className="material-symbols-outlined">leaderboard</span>
          <span className="nav-label">Classifica</span>
        </NavLink>
      </nav>

      {/* CENTRO: Search */}
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

      {/* DESTRA: Login/Logout */}
      <div className="login-container">
        {!isLoggedIn ? (
          <button
            type="button"
            className="login-button"
            onClick={handleLogin}
            disabled={!config}
          >
            Login
          </button>
        ) : (
          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
            disabled={!config}
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
