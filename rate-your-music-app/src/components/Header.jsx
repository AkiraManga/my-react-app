import React, { useEffect, useState } from 'react';
import '../styles/Header.css';

const Header = () => {
  const clientId = "351b8dq8eqn48qcqo23o5kio15";
  const domain = "https://rateyourmusic101.auth.eu-west-3.amazoncognito.com";
  const redirectUri = "http://localhost:5173/callback";
  const logoutRedirect = "http://localhost:5173";
  const responseType = "code";
  const scope = "openid profile email";

  const [isLoggedIn, setIsLoggedIn] = useState(false);

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
    const loginUrl = `${domain}/login?client_id=${clientId}&response_type=${responseType}&scope=${encodeURIComponent(
      scope
    )}&redirect_uri=${encodeURIComponent(redirectUri)}`;
    window.location.href = loginUrl;
  };

  const handleLogout = () => {
  sessionStorage.removeItem("id_token");
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");

    setIsLoggedIn(false);

  const logoutUrl = `${domain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(
    logoutRedirect
  )}`;
  window.location.href = logoutUrl;
};

  return (
    <header className="main-header">
      <div className="search-container">
        <input type="text" placeholder="Cerca album..." className="search-bar" />
      </div>
      <div className="login-container">
        {!isLoggedIn ? (
          <button className="login-button" onClick={handleLogin}>Login</button>
        ) : (
          <button className="logout-button" onClick={handleLogout}>Logout</button>
        )}
      </div>
    </header>
  );
};

export default Header;