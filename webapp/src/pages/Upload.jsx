import React, { useState } from 'react';
import Button from '../components/Button';

const Upload = () => {
    const [file, setFile] = useState(null);
    const [scanning, setScanning] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleDrop = (e) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            setFile(droppedFile);
            setResult(null);
            setError(null);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const parseFasta = (content) => {
        const lines = content.split('\n');
        let sequence = '';
        for (const line of lines) {
            if (!line.startsWith('>') && line.trim()) {
                sequence += line.trim();
            }
        }
        return sequence;
    };

    const handleAnalyze = async () => {
        if (!file) return;
        setScanning(true);
        setError(null);
        setResult(null);

        try {
            const content = await file.text();
            const sequence = parseFasta(content);

            if (!sequence) {
                throw new Error('No valid DNA sequence found in FASTA file.');
            }

            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sequence }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Analysis failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setScanning(false);
        }
    };

    const isMalicious = (data) => {
        // Simple heuristic based on available metrics (Layer 1 & 3)
        if (!data) return false;
        const highIdentity = data.layer1.top_hit && data.layer1.top_hit.identity > 90;
        const highCAI = data.layer3.max_cai > 0.8;
        return highIdentity || highCAI;
    };

    return (
        <div className="container mt-lg flex flex-col items-center">
            <h1 className="mb-lg">DETECT MALICIOUS GENOME</h1>

            <div
                className={`upload-zone ${file ? 'has-file' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
            >
                {scanning && <div className="scan-line"></div>}

                {!file ? (
                    <div className="text-center">
                        <div className="icon mb-lg">🧬</div>
                        <p className="text-muted">DRAG & DROP FASTA FILE HERE</p>
                        <p className="text-sm text-muted mt-lg">OR CLICK TO BROWSE</p>
                        <input
                            type="file"
                            className="file-input"
                            accept=".fasta,.fa,.txt"
                            onChange={(e) => {
                                if (e.target.files[0]) {
                                    setFile(e.target.files[0]);
                                    setResult(null);
                                    setError(null);
                                }
                            }}
                        />
                    </div>
                ) : (
                    <div className="text-center">
                        <div className="icon mb-lg">📄</div>
                        <p>{file.name}</p>
                        <p className="text-sm text-muted">{(file.size / 1024).toFixed(2)} KB</p>
                        <button
                            className="text-primary text-sm mt-lg underline"
                            onClick={(e) => {
                                e.stopPropagation();
                                setFile(null);
                                setResult(null);
                                setError(null);
                            }}
                        >
                            REMOVE
                        </button>
                    </div>
                )}
            </div>

            {file && !scanning && !result && (
                <Button onClick={handleAnalyze} className="mt-lg">
                    INITIATE SCAN
                </Button>
            )}

            {scanning && (
                <div className="mt-lg text-primary animate-pulse">
                    ANALYZING SEQUENCE PATTERNS...
                </div>
            )}

            {error && (
                <div className="mt-lg text-secondary">
                    ERROR: {error}
                </div>
            )}

            {result && (
                <div className={`result-card mt-lg ${isMalicious(result) ? 'malicious' : 'safe'}`}>
                    <h2 className="mb-lg">{isMalicious(result) ? 'THREAT DETECTED' : 'GENOME SECURE'}</h2>

                    <div className="metrics-grid text-left">
                        <div className="metric-group">
                            <h3 className="text-sm text-muted mb-sm">LAYER 1: BLAST</h3>
                            <p>GC Content: <span className="text-primary">{result.layer1.gc_content.toFixed(2)}%</span></p>
                            <p>Hits: <span className="text-primary">{result.layer1.num_hits}</span></p>
                            {result.layer1.top_hit && (
                                <p className="text-xs text-muted mt-xs">
                                    Top Hit: {result.layer1.top_hit.subject_title.substring(0, 30)}...
                                </p>
                            )}
                        </div>

                        <div className="metric-group">
                            <h3 className="text-sm text-muted mb-sm">LAYER 3: CAI</h3>
                            <p>Max CAI: <span className="text-primary">{result.layer3.max_cai?.toFixed(3) || 'N/A'}</span></p>
                        </div>
                    </div>

                    <Button onClick={() => { setFile(null); setResult(null); setError(null); }} className="mt-lg" variant={isMalicious(result) ? 'danger' : 'primary'}>
                        ANALYZE ANOTHER
                    </Button>
                </div>
            )}

            <style>{`
        .upload-zone {
          width: 100%;
          max-width: 600px;
          height: 300px;
          border: 2px dashed var(--color-border);
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          background: rgba(255, 255, 255, 0.02);
          position: relative;
          overflow: hidden;
          cursor: pointer;
        }
        .upload-zone:hover, .upload-zone.has-file {
          border-color: var(--color-primary);
          background: rgba(0, 255, 65, 0.05);
        }
        .file-input {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          opacity: 0;
          cursor: pointer;
        }
        .icon {
          font-size: 3rem;
        }
        .scan-line {
          position: absolute;
          left: 0;
          width: 100%;
          height: 2px;
          background: var(--color-primary);
          box-shadow: 0 0 10px var(--color-primary);
          animation: scan 2s linear infinite;
        }
        .result-card {
          padding: var(--spacing-lg);
          border-radius: var(--radius-md);
          text-align: center;
          width: 100%;
          max-width: 800px;
          animation: pulse 0.5s ease-out;
        }
        .result-card.safe {
          border: 1px solid var(--color-primary);
          background: rgba(0, 255, 65, 0.1);
        }
        .result-card.safe h2 {
          color: var(--color-primary);
        }
        .result-card.malicious {
          border: 1px solid var(--color-secondary);
          background: rgba(255, 0, 51, 0.1);
        }
        .result-card.malicious h2 {
          color: var(--color-secondary);
        }
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: var(--spacing-md);
          margin-top: var(--spacing-md);
          background: rgba(0, 0, 0, 0.3);
          padding: var(--spacing-md);
          border-radius: var(--radius-sm);
        }
        .metric-group p {
          font-family: var(--font-mono);
          font-size: 0.9rem;
          margin-bottom: var(--spacing-xs);
        }
        .text-xs { font-size: 0.75rem; }
        .mb-sm { margin-bottom: var(--spacing-sm); }
        .mt-xs { margin-top: var(--spacing-xs); }
        .underline { text-decoration: underline; }
      `}</style>
        </div>
    );
};

export default Upload;
