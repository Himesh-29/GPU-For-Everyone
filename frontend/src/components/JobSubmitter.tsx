import React, { useState } from 'react';

const JobSubmitter: React.FC = () => {
    const [prompt, setPrompt] = useState('');
    const [status, setStatus] = useState('');
    const [jobId, setJobId] = useState('');

    const handleSubmit = async () => {
        setStatus('Submitting...');
        try {
            const response = await fetch('http://localhost:8000/api/computing/submit-job/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'Authorization': 'Bearer ...' // Add token if auth enabled
                },
                body: JSON.stringify({
                    prompt: prompt,
                    model: 'llama3.2:latest'
                })
            });
            const data = await response.json();
            if (response.ok) {
                setStatus(`Job Submitted! ID: ${data.job_id}`);
                setJobId(data.job_id);
            } else {
                setStatus(`Error: ${data.error}`);
            }
        } catch (e) {
            setStatus(`Network Error: ${e}`);
        }
    };

    return (
        <div className="p-4 border rounded shadow-md bg-white max-w-md mx-auto mt-10">
            <h2 className="text-xl font-bold mb-4">Rent a GPU (Ollama)</h2>
            <textarea
                className="w-full p-2 border rounded mb-4"
                placeholder="Enter prompt for Llama 3..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
            />
            <button
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
                onClick={handleSubmit}
            >
                Submit Job (Cost: 5 Credits)
            </button>
            {status && <p className="mt-4 text-sm text-gray-700">{status}</p>}
        </div>
    );
};

export default JobSubmitter;
