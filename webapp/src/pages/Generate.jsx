import React, { useState } from 'react';
import Button from '../components/Button';

const Generate = () => {
    const [generating, setGenerating] = useState(false);
    const [output, setOutput] = useState('');

    const handleGenerate = () => {
        setGenerating(true);
        setOutput('');

        // Simulate generation streaming
        const sequence = "ATGC".repeat(20) + "GATTACA" + "CGTA".repeat(10);
        let i = 0;
        const interval = setInterval(() => {
            setOutput(prev => prev + sequence[i]);
            i++;
            if (i >= sequence.length) {
                clearInterval(interval);
                setGenerating(false);
            }
        }, 50);
    };

    return (
        <div className="container mt-lg flex flex-col items-center">
            <h1 className="mb-lg">GENERATE MALICIOUS PAYLOAD</h1>
            <p className="text-muted text-center mb-lg" style={{ maxWidth: '600px' }}>
                WARNING: This tool generates synthetic genome sequences with potential pathogenic markers.
                For red team research purposes only.
            </p>

            <div className="controls flex gap-md mb-lg">
                <div className="control-group">
                    <label className="text-sm text-muted">VIRAL VECTOR</label>
                    <select className="select-input">
                        <option>Adenovirus Type 5</option>
                        <option>Lentivirus</option>
                        <option>Retrovirus</option>
                    </select>
                </div>
                <div className="control-group">
                    <label className="text-sm text-muted">PAYLOAD TYPE</label>
                    <select className="select-input">
                        <option>Cytotoxicity</option>
                        <option>Immune Evasion</option>
                        <option>Replication Boost</option>
                    </select>
                </div>
            </div>

            <Button onClick={handleGenerate} disabled={generating}>
                {generating ? 'SYNTHESIZING...' : 'GENERATE SEQUENCE'}
            </Button>

            <div className="output-console mt-lg">
                <div className="console-header flex justify-between">
                    <span className="text-sm text-muted">OUTPUT.FASTA</span>
                    <span className="text-sm text-primary">{generating ? 'ACTIVE' : 'READY'}</span>
                </div>
                <pre className="console-body">
                    {output || <span className="text-muted opacity-50">// Awaiting generation command...</span>}
                    {generating && <span className="cursor">_</span>}
                </pre>
            </div>

            <style>{`
        .select-input {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          color: var(--color-text);
          padding: var(--spacing-sm) var(--spacing-md);
          border-radius: var(--radius-sm);
          font-family: var(--font-mono);
          min-width: 200px;
          margin-top: var(--spacing-xs);
        }
        .select-input:focus {
          outline: none;
          border-color: var(--color-primary);
        }
        .output-console {
          width: 100%;
          max-width: 800px;
          background: #000;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          overflow: hidden;
        }
        .console-header {
          padding: var(--spacing-sm) var(--spacing-md);
          background: var(--color-bg-secondary);
          border-bottom: 1px solid var(--color-border);
        }
        .console-body {
          padding: var(--spacing-md);
          min-height: 200px;
          font-family: var(--font-mono);
          font-size: 0.9rem;
          color: var(--color-primary);
          white-space: pre-wrap;
          word-break: break-all;
        }
        .cursor {
          animation: pulse 1s infinite;
        }
        .opacity-50 { opacity: 0.5; }
      `}</style>
        </div>
    );
};

export default Generate;
