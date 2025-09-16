import React from 'react';
import '../styles/Header.css';

const Header = () => {
  return (
    <header className="main-header">
      <div className="search-container">
        <input type="text" placeholder="Cerca album..." className="search-bar" />
      </div>
      <div className="login-container">
        <button className="login-button">Login</button>
      </div>
    </header>
  );
};

export default Header;
