import React, { useState, useEffect } from "react";
import apiService from "../services/api";
import "./VideoList.css";

const VideoList = ({ refreshTrigger, onDeleteSuccess, onDeleteError }) => {
  const [videos, setVideos] = useState([]);
  const [audio, setAudio] = useState([]);
  const [results, setResults] = useState([]);
  const [temp, setTemp] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState({});
  const [previewMedia, setPreviewMedia] = useState(null);
  const [downloading, setDownloading] = useState({});

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getMedia();
      setVideos(data.videos || []);
      setAudio(data.audio || []);
      setResults(data.results || []);
      setTemp(data.temp || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, [refreshTrigger]);

  const handleDelete = async (filename, source = "videos") => {
    try {
      setDeleting((prev) => ({ ...prev, [filename]: true }));
      await apiService.deleteMedia(filename, source);
      setVideos((prev) => prev.filter((video) => video !== filename));
      setAudio((prev) => prev.filter((audioFile) => audioFile !== filename));
      setResults((prev) => prev.filter((result) => result !== filename));
      setTemp((prev) => prev.filter((tempFile) => tempFile !== filename));
      onDeleteSuccess?.(`Media file "${filename}" deleted successfully`);
    } catch (err) {
      onDeleteError?.(err.message);
    } finally {
      setDeleting((prev) => ({ ...prev, [filename]: false }));
    }
  };

  const handleDownload = async (filename, source = "results") => {
    try {
      setDownloading((prev) => ({ ...prev, [filename]: true }));
      const blob = await apiService.downloadVideo(filename, source);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      onDeleteError?.(err.message);
    } finally {
      setDownloading((prev) => ({ ...prev, [filename]: false }));
    }
  };

  const handlePreview = (filename, source = "results") => {
    const mediaUrl = apiService.getDownloadUrl(filename, source);
    setPreviewMedia({ filename, url: mediaUrl, source });
  };

  const closePreview = () => {
    setPreviewMedia(null);
  };

  const getFileIcon = (filename) => {
    const extension = filename.split(".").pop()?.toLowerCase();
    const videoIconMap = {
      mp4: "🎬",
      avi: "🎥",
      mov: "📹",
      mkv: "🎞️",
      webm: "📽️",
    };
    const audioIconMap = {
      mp3: "🎵",
      wav: "🎶",
      aac: "🎼",
      flac: "🎹",
      ogg: "🎧",
      m4a: "🎤",
      wma: "🎙️",
    };
    return videoIconMap[extension] || audioIconMap[extension] || "📁";
  };

  const isAudioFile = (filename) => {
    const extension = filename.split(".").pop()?.toLowerCase();
    return ["mp3", "wav", "aac", "flac", "ogg", "m4a", "wma"].includes(
      extension
    );
  };

  if (loading) {
    return (
      <div className="video-list">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading media files...</p>
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
        <h2>Media Files in Container</h2>
        <button onClick={fetchVideos} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {videos.length === 0 &&
      audio.length === 0 &&
      results.length === 0 &&
      temp.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📁</div>
          <p>No media files found in container</p>
          <span>Upload a video or audio file to get started</span>
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
                            {video.split(".").pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handlePreview(video, "videos")}
                        className="preview-btn"
                        title="Preview video"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(video, "videos")}
                        disabled={downloading[video]}
                        className="download-btn"
                        title="Download video"
                      >
                        {downloading[video] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(video, "videos")}
                        disabled={deleting[video]}
                        className="delete-btn"
                        title="Delete video"
                      >
                        {deleting[video] ? "⏳" : "🗑️"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {audio.length > 0 && (
            <div className="video-section">
              <h3>🎵 Uploaded Audio ({audio.length})</h3>
              <div className="video-grid">
                {audio.map((audioFile, index) => (
                  <div key={index} className="video-item">
                    <div className="video-info">
                      <div className="video-icon">{getFileIcon(audioFile)}</div>
                      <div className="video-details">
                        <div className="video-name" title={audioFile}>
                          {audioFile}
                        </div>
                        <div className="video-meta">
                          <span className="video-type">
                            {audioFile.split(".").pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handlePreview(audioFile, "videos")}
                        className="preview-btn"
                        title="Preview audio"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(audioFile, "videos")}
                        disabled={downloading[audioFile]}
                        className="download-btn"
                        title="Download audio"
                      >
                        {downloading[audioFile] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(audioFile, "videos")}
                        disabled={deleting[audioFile]}
                        className="delete-btn"
                        title="Delete audio"
                      >
                        {deleting[audioFile] ? "⏳" : "🗑️"}
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
                            {result.split(".").pop().toUpperCase()}
                          </span>
                          <span className="result-badge">Processed</span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handlePreview(result, "results")}
                        className="preview-btn"
                        title="Preview video"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(result, "results")}
                        disabled={downloading[result]}
                        className="download-btn"
                        title="Download video"
                      >
                        {downloading[result] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(result, "results")}
                        disabled={deleting[result]}
                        className="delete-btn"
                        title="Delete result"
                      >
                        {deleting[result] ? "⏳" : "🗑️"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {temp.length > 0 && (
            <div className="video-section">
              <h3>🗂️ Temporary Files ({temp.length})</h3>
              <div className="video-grid">
                {temp.map((tempFile, index) => (
                  <div key={index} className="video-item temp-item">
                    <div className="video-info">
                      <div className="video-icon">{getFileIcon(tempFile)}</div>
                      <div className="video-details">
                        <div className="video-name" title={tempFile}>
                          {tempFile}
                        </div>
                        <div className="video-meta">
                          <span className="video-type">
                            {tempFile.split(".").pop().toUpperCase()}
                          </span>
                          <span className="temp-badge">Temporary</span>
                        </div>
                      </div>
                    </div>
                    <div className="video-actions">
                      <button
                        onClick={() => handlePreview(tempFile, "temp")}
                        className="preview-btn"
                        title="Preview video"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(tempFile, "temp")}
                        disabled={downloading[tempFile]}
                        className="download-btn"
                        title="Download video"
                      >
                        {downloading[tempFile] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(tempFile, "temp")}
                        disabled={deleting[tempFile]}
                        className="delete-btn"
                        title="Delete temporary file"
                      >
                        {deleting[tempFile] ? "⏳" : "🗑️"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Media Preview Modal */}
      {previewMedia && (
        <div className="video-preview-modal" onClick={closePreview}>
          <div
            className="video-preview-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="video-preview-header">
              <h3>{previewMedia.filename}</h3>
              <button className="close-btn" onClick={closePreview}>
                ✕
              </button>
            </div>
            <div className="video-preview-player">
              {isAudioFile(previewMedia.filename) ? (
                <audio
                  controls
                  autoPlay
                  src={previewMedia.url}
                  style={{ width: "100%" }}
                >
                  Your browser does not support the audio tag.
                </audio>
              ) : (
                <video
                  controls
                  autoPlay
                  src={previewMedia.url}
                  style={{ width: "100%", height: "auto" }}
                >
                  Your browser does not support the video tag.
                </video>
              )}
            </div>
            <div className="video-preview-actions">
              <button
                onClick={() =>
                  handleDownload(previewMedia.filename, previewMedia.source)
                }
                disabled={downloading[previewMedia.filename]}
                className="download-btn"
              >
                {downloading[previewMedia.filename]
                  ? "⏳ Downloading..."
                  : "⬇️ Download"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoList;
