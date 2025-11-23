import React from 'react';

const Button = ({ children, onClick, variant = 'primary', className = '', ...props }) => {
    return (
        <button
            className={`btn btn-${variant} ${className}`}
            onClick={onClick}
            {...props}
        >
            {children}
            <style>{`
        .btn {
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: var(--radius-sm);
          font-family: var(--font-mono);
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s ease;
          text-transform: uppercase;
          letter-spacing: 1px;
          font-size: 0.9rem;
        }
        .btn-primary {
          background: var(--color-primary);
          color: #000;
          box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
        }
        .btn-primary:hover {
          background: #00cc33;
          box-shadow: 0 0 25px rgba(0, 255, 65, 0.5);
          transform: translateY(-1px);
        }
        .btn-secondary {
          background: transparent;
          border: 1px solid var(--color-primary);
          color: var(--color-primary);
        }
        .btn-secondary:hover {
          background: rgba(0, 255, 65, 0.1);
        }
        .btn-danger {
          background: var(--color-secondary);
          color: #fff;
          box-shadow: 0 0 15px rgba(255, 0, 51, 0.3);
        }
        .btn-danger:hover {
          background: #cc0029;
          box-shadow: 0 0 25px rgba(255, 0, 51, 0.5);
        }
      `}</style>
        </button>
    );
};

export default Button;
