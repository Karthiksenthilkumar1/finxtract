import React, { useState } from 'react';
import axios from 'axios';

function Results({ data, lastFileName }) {
    const [downloading, setDownloading] = useState(false);

    if (!data || (!data['Balance Sheet']?.length && !data['Profit and Loss']?.length)) {
        return (
            <div className="page-container centered">
                <div className="empty-state glass">
                    <h2>No Data Found</h2>
                    <p>Please upload a document in the Upload section first.</p>
                </div>
            </div>
        );
    }

    const handleDownload = async () => {
        // Note: In a real app, we'd send the file again or have a persistent session
        // For this demo, we can't easily re-upload the same 'File' object without storing it
        // But we can trigger the same logic if the user re-uploads or we just mock the link
        // Here we'll show a "Simulated Download" for the class project if actual file object is lost,
        // OR try to fetch from backend if the file is still in 'uploads/' (backend keeps it)

        setDownloading(true);
        try {
            // Assuming the backend still has the last file or we provide the name
            const response = await axios.get('http://localhost:8000/health'); // Just a check
            alert('In a production system, this would trigger the Excel download for: ' + lastFileName);
        } finally {
            setDownloading(false);
        }
    };

    const renderTable = (title, items) => {
        if (!items || items.length === 0) return null;
        return (
            <div className="data-section">
                <h3>{title}</h3>
                <div className="table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => (
                                <tr key={idx}>
                                    <td>{item.Description}</td>
                                    <td className="value-cell">{item.Value}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    return (
        <div className="page-container">
            <header className="page-header flex-header">
                <div>
                    <h2>Extracted Intelligence</h2>
                    <p style={{fontFamily: 'monospace', fontSize: '0.9rem', color: 'hsl(var(--primary))'}}>Source: {lastFileName || 'Verified Dataset'}</p>
                </div>
                <button onClick={handleDownload} className="primary-btn" style={{width: 'auto', margin: 0, padding: '10px 24px', background: 'transparent', border: '1px solid hsl(var(--primary))', color: 'hsl(var(--primary))'}}>
                    Export Dataset (XLSX)
                </button>
            </header>

            <div className="results-grid">
                {renderTable('Balance Sheet Intelligence', data['Balance Sheet'])}
                {renderTable('Performance (P&L) Data', data['Profit and Loss'])}
            </div>
        </div>
    );
}

export default Results;
