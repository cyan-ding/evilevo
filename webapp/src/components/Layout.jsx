import React from 'react';
import Navbar from './Navbar';

const Layout = ({ children }) => {
    return (
        <div className="layout">
            <Navbar />
            <main className="main-content">
                {children}
            </main>
            <footer className="footer text-center">
                <p className="text-muted text-sm">
                    &copy; 2025 EVILEVO CORP. <span className="text-primary">SECURE THE FUTURE.</span>
                </p>
            </footer>
            <style>{`
        .layout {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }
        .main-content {
          flex: 1;
          position: relative;
        }
        .footer {
          padding: var(--spacing-lg) 0;
          border-top: 1px solid var(--color-border);
          margin-top: auto;
        }
        .text-sm {
          font-size: 0.8rem;
        }
        .text-muted {
          color: var(--color-text-muted);
        }
      `}</style>
        </div>
    );
};

export default Layout;
