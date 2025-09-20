import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import '../styles/Header.css';

const Header = () => {
  const clientId = "351b8dq8eqn48qcqo23o5kio15";
  const domain = "https://rateyourmusic101.auth.eu-west-3.amazoncognito.com";
  const redirectUri = "https://dfxq4ov956y7j.cloudfront.net/callback";
  const logoutRedirect = "https://dfxq4ov956y7j.cloudfront.net";
  const responseType = "code";
  // 👇 identico al link che funziona, NIENTE encode su questa variabile
  const scope = "email+openid+profile";

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const token = sessionStorage.getItem("id_token");
    setIsLoggedIn(!!token);

    const handleStorageChange = () => {
      const newToken = sessionStorage.getItem("id_token");
      setIsLoggedIn(!!newToken);
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleLogin = () => {
    const loginUrl =
      `${domain}/login?client_id=${clientId}` +
      `&response_type=${responseType}` +
      `&scope=${scope}` + // <-- non encodare
      `&redirect_uri=${encodeURIComponent(redirectUri)}`;

    console.log("🔗 Login URL generato:", loginUrl);
    window.location.href = loginUrl;
  };

  const handleLogout = () => {
    const logoutUrl =
      `${domain}/logout?client_id=${clientId}` +
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
      <div className="search-container">
        <form onSubmit={handleSearch} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}>
          <input
            type="text"
            placeholder="Cerca album..."
            className="search-bar"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>
      </div>
      <div className="login-container">
        {!isLoggedIn ? (
          <button
            type="button"             // ✅ evita submit del form
            className="login-button"
            onClick={handleLogin}
          >
            Login
          </button>
        ) : (
          <button
            type="button"             // ✅ evita submit del form
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
