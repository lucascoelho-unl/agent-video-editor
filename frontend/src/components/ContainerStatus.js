import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './ContainerStatus.css';

const ContainerStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getContainerStatus();
      setStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh status every 60 seconds (less frequent to reduce API calls)
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="container-status">
        <div className="status-loading">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span>Checking container status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container-status">
        <div className="status-error">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <h4>Container Status Error</h4>
            <p>{error}</p>
            <button onClick={fetchStatus} className="retry-btn">
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isRunning = status?.container_running;
  const statusMessage = status?.message || 'Unknown status';

  return (
    <div className="container-status">
      <div className={`status-card ${isRunning ? 'running' : 'stopped'}`}>
        <div className="status-indicator">
          <div className={`status-dot ${isRunning ? 'running' : 'stopped'}`}></div>
          <span className="status-text">
            {isRunning ? 'Container Running' : 'Container Stopped'}
          </span>
        </div>
        <div className="status-details">
          <p className="status-message">{statusMessage}</p>
          {status?.container_id && (
            <p className="container-id">ID: {status.container_id}</p>
          )}
        </div>
        <button onClick={fetchStatus} className="refresh-btn" title="Refresh status">
          🔄
        </button>
      </div>
    </div>
  );
};

export default ContainerStatus;
