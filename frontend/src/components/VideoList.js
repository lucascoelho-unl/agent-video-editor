import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './VideoList.css';

const VideoList = ({ refreshTrigger, onDeleteSuccess, onDeleteError }) => {
  const [videos, setVideos] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState({});
  const [previewVideo, setPreviewVideo] = useState(null);
  const [downloading, setDownloading] = useState({});

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getVideos();
      setVideos(data.videos || []);
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, [refreshTrigger]);

  const handleDelete = async filename => {
    try {
      setDeleting(prev => ({ ...prev, [filename]: true }));
      await apiService.deleteVideo(filename);
      setVideos(prev => prev.filter(video => video !== filename));
      setResults(prev => prev.filter(result => result !== filename));
      onDeleteSuccess?.(`Video "${filename}" deleted successfully`);
    } catch (err) {
      onDeleteError?.(err.message);
    } finally {
      setDeleting(prev => ({ ...prev, [filename]: false }));
    }
  };

  const handleDownload = async filename => {
    try {
      setDownloading(prev => ({ ...prev, [filename]: true }));
      const blob = await apiService.downloadVideo(filename);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      onDeleteError?.(err.message);
    } finally {
      setDownloading(prev => ({ ...prev, [filename]: false }));
    }
  };

  const handlePreview = filename => {
    const videoUrl = apiService.getDownloadUrl(filename);
    setPreviewVideo({ filename, url: videoUrl });
  };

  const closePreview = () => {
    setPreviewVideo(null);
  };

  const getFileIcon = filename => {
    const extension = filename.split('.').pop()?.toLowerCase();
    const iconMap = {
      mp4: '🎬',
      avi: '🎥',
      mov: '📹',
      mkv: '🎞️',
      webm: '📽️',
    };
    return iconMap[extension] || '🎬';
  };

  if (loading) {
    return (
      <div className="video-list">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading videos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="video-list">
        <div className="error">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchVideos} className="retry-btn">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="video-list">
      <div className="list-header">
        <h2>Videos in Container</h2>
        <button onClick={fetchVideos} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {videos.length === 0 && results.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📁</div>
          <p>No videos found in container</p>
          <span>Upload a video to get started</span>
        </div>
      ) : (
        <div className="video-sections">
          {videos.length > 0 && (
            <div className="video-section">
              <h3>📤 Uploaded Videos ({videos.length})</h3>
              <div className="video-grid">
                {videos.map((video, index) => (
                  <div key={index} className="video-item">
                    <div className="video-info">
                      <div className="video-icon">{getFileIcon(video)}</div>
                      <div className="video-details">
                        <div className="video-name" title={video}>
                          {video}
                        </div>
                        <div className="video-meta">
                          <span className="video-type">
                            {video.split('.').pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handleDelete(video)}
                        disabled={deleting[video]}
                        className="delete-btn"
                        title="Delete video"
                      >
                        {deleting[video] ? '⏳' : '🗑️'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div className="video-section">
              <h3>📥 Processed Results ({results.length})</h3>
              <div className="video-grid">
                {results.map((result, index) => (
                  <div key={index} className="video-item result-item">
                    <div className="video-info">
                      <div className="video-icon">{getFileIcon(result)}</div>
                      <div className="video-details">
                        <div className="video-name" title={result}>
                          {result}
                        </div>
                        <div className="video-meta">
                          <span className="video-type">
                            {result.split('.').pop().toUpperCase()}
                          </span>
                          <span className="result-badge">Processed</span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handlePreview(result)}
                        className="preview-btn"
                        title="Preview video"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(result)}
                        disabled={downloading[result]}
                        className="download-btn"
                        title="Download video"
                      >
                        {downloading[result] ? '⏳' : '⬇️'}
                      </button>
                      <button
                        onClick={() => handleDelete(result)}
                        disabled={deleting[result]}
                        className="delete-btn"
                        title="Delete result"
                      >
                        {deleting[result] ? '⏳' : '🗑️'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Video Preview Modal */}
      {previewVideo && (
        <div className="video-preview-modal" onClick={closePreview}>
          <div
            className="video-preview-content"
            onClick={e => e.stopPropagation()}
          >
            <div className="video-preview-header">
              <h3>{previewVideo.filename}</h3>
              <button className="close-btn" onClick={closePreview}>
                ✕
              </button>
            </div>
            <div className="video-preview-player">
              <video
                controls
                autoPlay
                src={previewVideo.url}
                style={{ width: '100%', height: 'auto' }}
              >
                Your browser does not support the video tag.
              </video>
            </div>
            <div className="video-preview-actions">
              <button
                onClick={() => handleDownload(previewVideo.filename)}
                disabled={downloading[previewVideo.filename]}
                className="download-btn"
              >
                {downloading[previewVideo.filename]
                  ? '⏳ Downloading...'
                  : '⬇️ Download'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoList;
