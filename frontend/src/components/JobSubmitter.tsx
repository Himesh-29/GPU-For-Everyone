import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const JobSubmitter: React.FC = () => {
    const { token } = useAuth();
    const [prompt, setPrompt] = useState('');
    const [model, setModel] = useState('llama3.2:latest');
    const [status, setStatus] = useState('');
    const [result, setResult] = useState('');
    const [jobId, setJobId] = useState<number | null>(null);
    const [polling, setPolling] = useState(false);

    const handleSubmit = async () => {
        if (!prompt.trim()) {
            setStatus('Please enter a prompt.');
            return;
        }
        setStatus('Submitting...');
        setResult('');
        setJobId(null);

        try {
            const response = await axios.post(
                `${API_URL}/api/computing/submit-job/`,
                { prompt, model },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setStatus(`Job #${response.data.job_id} submitted! Waiting for result...`);
            setJobId(response.data.job_id);
            pollJobResult(response.data.job_id);
        } catch (err: any) {
            const msg = err.response?.data?.error || err.message;
            setStatus(`Error: ${msg}`);
        }
    };

    const pollJobResult = async (id: number) => {
        setPolling(true);
        const maxAttempts = 60;
        for (let i = 0; i < maxAttempts; i++) {
            try {
                const resp = await axios.get(
                    `${API_URL}/api/computing/jobs/${id}/`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                if (resp.data.status === 'COMPLETED') {
                    setStatus(`✅ Job #${id} completed!`);
                    setResult(resp.data.result?.output || JSON.stringify(resp.data.result));
                    setPolling(false);
                    return;
                } else if (resp.data.status === 'FAILED') {
                    setStatus(`❌ Job #${id} failed`);
                    setResult(resp.data.result?.error || 'Unknown error');
                    setPolling(false);
                    return;
                }
            } catch {
                // ignore polling errors
            }
            await new Promise(r => setTimeout(r, 2000));
        }
        setStatus(`⏱ Job #${id} timed out waiting for result.`);
        setPolling(false);
    };

    return (
        <div className="glass-card">
            <h3>Submit a Job</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
                <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    style={{
                        padding: '10px 14px', borderRadius: '8px',
                        background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(197,160,89,0.3)',
                        color: '#333', fontSize: '14px', fontFamily: 'inherit'
                    }}
                >
                    <option value="llama3.2:latest">🦙 Llama 3.2 (2GB)</option>
                    <option value="gemma3:270m">💎 Gemma 3 270M (291MB)</option>
                </select>

                <textarea
                    placeholder="Enter your prompt..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={3}
                    style={{
                        padding: '10px 14px', borderRadius: '8px',
                        background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(197,160,89,0.3)',
                        color: '#333', resize: 'vertical', fontSize: '14px',
                        fontFamily: 'inherit'
                    }}
                />

                <button
                    className="btn-primary"
                    onClick={handleSubmit}
                    disabled={polling || !prompt.trim()}
                    style={{ opacity: polling ? 0.6 : 1, width: '100%' }}
                >
                    {polling ? '⏳ Processing...' : '🚀 Submit Job (1 Credit)'}
                </button>

                {status && (
                    <div style={{
                        padding: '10px 14px', borderRadius: '8px',
                        background: status.includes('Error') || status.includes('❌')
                            ? 'rgba(220,38,38,0.08)'
                            : status.includes('✅')
                                ? 'rgba(34,197,94,0.08)'
                                : 'rgba(197,160,89,0.08)',
                        border: '1px solid rgba(197,160,89,0.2)',
                        fontSize: '13px', color: '#555'
                    }}>
                        {status}
                    </div>
                )}

                {result && (
                    <div style={{
                        padding: '14px', borderRadius: '8px',
                        background: 'rgba(255,255,255,0.8)',
                        border: '1px solid rgba(197,160,89,0.3)',
                        whiteSpace: 'pre-wrap', fontSize: '13px',
                        color: '#333', lineHeight: '1.5',
                        maxHeight: '300px', overflowY: 'auto'
                    }}>
                        <strong style={{ color: 'var(--color-gold)' }}>LLM Response:</strong>
                        <br />{result}
                    </div>
                )}
            </div>
        </div>
    );
};

export default JobSubmitter;
