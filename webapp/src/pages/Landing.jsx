import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/Button';

const Landing = () => {
    return (
        <div className="landing container flex flex-col items-center justify-center text-center">
            <div className="dna-container">
                {[...Array(20)].map((_, i) => (
                    <div key={i} className="dna-strand" style={{ animationDelay: `${i * 0.1}s` }}></div>
                ))}
            </div>

            <div className="hero-content">
                <h1 className="hero-title">
                    DETECT. <span className="text-primary">ANALYZE.</span> PREVENT.
                </h1>
                <p className="hero-subtitle text-muted mt-lg mb-lg">
                    Advanced genome sequencing analysis for malicious pattern detection.
                    Secure your biological data with next-gen AI.
                </p>
                <div className="flex gap-md justify-center">
                    <Link to="/upload">
                        <Button variant="primary">Start Detection</Button>
                    </Link>
                    <Link to="/generate">
                        <Button variant="secondary">Generate Sample</Button>
                    </Link>
                </div>
            </div>
            <style>{`
        .landing {
          min-height: 80vh;
          position: relative;
          overflow: hidden;
        }
        .hero-content {
          position: relative;
          z-index: 10;
          background: rgba(5, 5, 5, 0.6);
          padding: 2rem;
          border-radius: 20px;
          backdrop-filter: blur(5px);
        }
        .hero-title {
          font-size: 4rem;
          letter-spacing: -2px;
          margin-bottom: var(--spacing-md);
          text-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        }
        .hero-subtitle {
          font-size: 1.2rem;
          max-width: 600px;
          margin-left: auto;
          margin-right: auto;
        }
        .dna-container {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%) rotate(-45deg);
          width: 600px;
          height: 800px;
          display: flex;
          justify-content: space-between;
          opacity: 0.2;
          z-index: 0;
          pointer-events: none;
        }
        .dna-strand {
          width: 2px;
          height: 100%;
          background: linear-gradient(to bottom, transparent, var(--color-primary), transparent);
          animation: pulse 3s infinite ease-in-out;
        }
        @keyframes pulse {
          0% {
            transform: scaleY(0.8);
            opacity: 0.5;
          }
          50% {
            transform: scaleY(1);
            opacity: 1;
          }
          100% {
            transform: scaleY(0.8);
            opacity: 0.5;
          }
        }
      `}</style>
        </div>
    );
};

export default Landing;
