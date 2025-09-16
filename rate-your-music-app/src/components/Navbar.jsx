import React from 'react';
import '../styles/Navbar.css'; // Assuming you have a CSS file for styling

function Navbar() {
  return (
    <nav className="navbar">
      <div className="logo">🎵 RateYourMusic</div>
      <input type="text" className="search" placeholder="Cerca album..." />
      <button className="login-btn">Login</button>
    </nav>
  );
}

export default Navbar;
