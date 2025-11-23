import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
    const location = useLocation();

    const isActive = (path) => {
        return location.pathname === path ? 'text-primary' : 'text-muted';
    };

    return (
        <nav className="navbar">
            <div className="container flex justify-between items-center">
                <Link to="/" className="logo">
                    <span className="text-primary">EVIL</span>EVO
                </Link>
                <div className="nav-links flex gap-lg">
                    <Link to="/" className={`nav-link ${isActive('/')}`}>HOME</Link>
                    <Link to="/upload" className={`nav-link ${isActive('/upload')}`}>DETECT</Link>
                    <Link to="/generate" className={`nav-link ${isActive('/generate')}`}>GENERATE</Link>
                </div>
            </div>
            <style>{`
        .navbar {
          padding: var(--spacing-md) 0;
          border-bottom: 1px solid var(--color-border);
          background: rgba(5, 5, 5, 0.8);
          backdrop-filter: blur(10px);
          position: sticky;
          top: 0;
          z-index: 100;
        }
        .logo {
          font-family: var(--font-mono);
          font-weight: 700;
          font-size: 1.5rem;
          letter-spacing: -1px;
          color: #fff;
        }
        .nav-link {
          font-family: var(--font-mono);
          font-size: 0.9rem;
          letter-spacing: 1px;
          color: var(--color-text-muted);
        }
        .nav-link:hover, .nav-link.text-primary {
          color: var(--color-primary);
        }
      `}</style>
        </nav>
    );
};

export default Navbar;
