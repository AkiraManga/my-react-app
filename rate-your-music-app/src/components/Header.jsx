import React from 'react';
import '../styles/Header.css';

const Header = () => {
  const handleLogin = () => {
    const clientId = "2le29e7no48i21s6oonqa4v8ib";  // ID client Cognito
    const domain = "https://rateyourmusic101.auth.eu-west-3.amazoncognito.com"; // dominio Cognito
    const redirectUri = "http://localhost:5173/callback"; // deve essere registrato in Cognito
    const responseType = "code";
    const scope = "openid profile email";

    const loginUrl = `${domain}/login?client_id=${clientId}&response_type=${responseType}&scope=${encodeURIComponent(
      scope
    )}&redirect_uri=${encodeURIComponent(redirectUri)}`;

    console.log("Redirecting to:", loginUrl);
    window.location.href = loginUrl;
  };

  return (
    <header className="main-header">
      <div className="search-container">
        <input type="text" placeholder="Cerca album..." className="search-bar" />
      </div>
      <div className="login-container">
        <button className="login-button" onClick={handleLogin}>Login</button>
      </div>
    </header>
  );
};

export default Header;
