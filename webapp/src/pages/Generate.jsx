import React, { useState, useEffect } from 'react';
import Button from '../components/Button';

const Generate = () => {
    const [generating, setGenerating] = useState(false);
    const [output, setOutput] = useState('');
    const [metrics, setMetrics] = useState(null);
    const [error, setError] = useState(null);

    // Parameters
    const [checkpoints, setCheckpoints] = useState([]);
    const [selectedCheckpoint, setSelectedCheckpoint] = useState('');
    const [prompt, setPrompt] = useState('AATTTAAATCTAATTATAAAAAAGCCAATTAAACCTGTAAATGGATACTTTTTTCATTCAATCTTTTAAG');
    const [maxTokens, setMaxTokens] = useState(1024);
    const [temperature, setTemperature] = useState(1.0);

    useEffect(() => {
        fetchCheckpoints();
    }, []);

    const fetchCheckpoints = async () => {
        try {
            const response = await fetch('/checkpoints');
            if (response.ok) {
                const data = await response.json();
                setCheckpoints(data.checkpoints || []);
                if (data.checkpoints && data.checkpoints.length > 0) {
                    setSelectedCheckpoint(data.checkpoints[0]);
                }
            }
        } catch (err) {
            console.error('Failed to fetch checkpoints:', err);
            setError('Failed to load model checkpoints. Is the inference server running?');
        }
    };

    const handleGenerate = async () => {
        if (!selectedCheckpoint) {
            setError('Please select a model checkpoint.');
            return;
        }

        setGenerating(true);
        setOutput('');
        setMetrics(null);
        setError(null);

        try {
            const response = await fetch('/inference', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ckpt_dir: selectedCheckpoint,
                    prompt: prompt,
                    max_new_tokens: parseInt(maxTokens),
                    temperature: parseFloat(temperature)
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Generation failed');
            }

            const data = await response.json();
            setOutput(data.generated_text);
            setMetrics({
                time: data.inference_time_seconds,
                rate: data.tokens_per_second,
                length: data.generated_length
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="container mt-lg flex flex-col items-center">
            <h1 className="mb-lg">GENERATE MALICIOUS PAYLOAD</h1>
            <p className="text-muted text-center mb-lg" style={{ maxWidth: '600px' }}>
                WARNING: This tool generates synthetic genome sequences with potential pathogenic markers.
                For red team research purposes only.
            </p>

            <div className="controls-grid mb-lg">
                <div className="control-group full-width">
                    <label className="text-sm text-muted">MODEL CHECKPOINT</label>
                    <select
                        className="select-input"
                        value={selectedCheckpoint}
                        onChange={(e) => setSelectedCheckpoint(e.target.value)}
                    >
                        {checkpoints.length === 0 && <option>Loading checkpoints...</option>}
                        {checkpoints.map((ckpt, i) => (
                            <option key={i} value={ckpt}>{ckpt.split('/').pop()}</option>
                        ))}
                    </select>
                </div>

                <div className="control-group full-width">
                    <label className="text-sm text-muted">PROMPT</label>
                    <textarea
                        className="text-input"
                        rows="3"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                    />
                </div>

                <div className="control-group">
                    <label className="text-sm text-muted">MAX TOKENS: <span className="text-primary">{maxTokens}</span></label>
                    <input
                        type="range"
                        min="64"
                        max="4096"
                        step="64"
                        value={maxTokens}
                        onChange={(e) => setMaxTokens(e.target.value)}
                        className="range-input"
                    />
                </div>

                <div className="control-group">
                    <label className="text-sm text-muted">TEMPERATURE: <span className="text-primary">{temperature}</span></label>
                    <input
                        type="range"
                        min="0.1"
                        max="2.0"
                        step="0.1"
                        value={temperature}
                        onChange={(e) => setTemperature(e.target.value)}
                        className="range-input"
                    />
                </div>
            </div>

            <Button onClick={handleGenerate} disabled={generating || !selectedCheckpoint}>
                {generating ? 'SYNTHESIZING...' : 'GENERATE SEQUENCE'}
            </Button>

            {error && (
                <div className="mt-lg text-secondary">
                    ERROR: {error}
                </div>
            )}

            <div className="output-console mt-lg">
                <div className="console-header flex justify-between">
                    <span className="text-sm text-muted">OUTPUT.FASTA</span>
                    <div className="flex gap-md">
                        {metrics && (
                            <>
                                <span className="text-sm text-muted">{metrics.time.toFixed(2)}s</span>
                                <span className="text-sm text-muted">{metrics.rate.toFixed(1)} tok/s</span>
                            </>
                        )}
                        <span className="text-sm text-primary">{generating ? 'ACTIVE' : 'READY'}</span>
                    </div>
                </div>
                <pre className="console-body">
                    {output || <span className="text-muted opacity-50">// Awaiting generation command...</span>}
                    {generating && <span className="cursor">_</span>}
                </pre>
            </div>

            <style>{`
        .controls-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--spacing-md);
          width: 100%;
          max-width: 800px;
        }
        .full-width {
          grid-column: 1 / -1;
        }
        .select-input, .text-input {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          color: var(--color-text);
          padding: var(--spacing-sm) var(--spacing-md);
          border-radius: var(--radius-sm);
          font-family: var(--font-mono);
          width: 100%;
          margin-top: var(--spacing-xs);
        }
        .select-input:focus, .text-input:focus {
          outline: none;
          border-color: var(--color-primary);
        }
        .range-input {
          width: 100%;
          margin-top: var(--spacing-sm);
          accent-color: var(--color-primary);
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
          max-height: 500px;
          overflow-y: auto;
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
