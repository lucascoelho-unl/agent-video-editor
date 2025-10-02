import React, { useState, useEffect } from "react";
import apiService from "../services/api";
import "./MediaList.css";

const MediaList = ({ refreshTrigger, onDeleteSuccess, onDeleteError }) => {
  const [media, setMedia] = useState([]);
  const [videos, setVideos] = useState([]);
  const [audio, setAudio] = useState([]);
  const [images, setImages] = useState([]);
  const [results, setResults] = useState([]);
  const [temp, setTemp] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState({});
  const [previewMedia, setPreviewMedia] = useState(null);
  const [downloading, setDownloading] = useState({});

  const fetchMedia = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getMedia();
      setMedia(data.medias || []);
      setResults(data.results || []);
      setTemp(data.temp || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedia();
  }, [refreshTrigger]);

  useEffect(() => {
    const videoFiles = media.filter((file) => isVideoFile(file));
    const audioFiles = media.filter((file) => isAudioFile(file));
    const imageFiles = media.filter((file) => isImageFile(file));

    setVideos(videoFiles);
    setAudio(audioFiles);
    setImages(imageFiles);
  }, [media]);

  const handleDelete = async (filename, source = "medias") => {
    try {
      setDeleting((prev) => ({ ...prev, [filename]: true }));
      await apiService.deleteMedia(filename, source);
      setMedia((prev) => prev.filter((media) => media !== filename));
      setResults((prev) => prev.filter((result) => result !== filename));
      setTemp((prev) => prev.filter((tempFile) => tempFile !== filename));
      onDeleteSuccess?.(`Media file "${filename}" deleted successfully`);
    } catch (err) {
      onDeleteError?.(err.message);
    } finally {
      setDeleting((prev) => ({ ...prev, [filename]: false }));
    }
  };

  const handleDownload = async (filename, source = "medias") => {
    try {
      setDownloading((prev) => ({ ...prev, [filename]: true }));
      const blob = await apiService.downloadMedia(filename, source);
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

  const handlePreview = (filename, source = "medias") => {
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
    const imageIconMap = {
      jpg: "🖼️",
      jpeg: "🖼️",
      png: "🖼️",
      gif: "🖼️",
      bmp: "🖼️",
      tiff: "🖼️",
    };
    return (
      videoIconMap[extension] ||
      audioIconMap[extension] ||
      imageIconMap[extension] ||
      "📁"
    );
  };

  const isVideoFile = (filename) => {
    const extension = filename.split(".").pop()?.toLowerCase();
    return ["mp4", "avi", "mov", "mkv", "webm"].includes(extension);
  };

  const isAudioFile = (filename) => {
    const extension = filename.split(".").pop()?.toLowerCase();
    return ["mp3", "wav", "aac", "flac", "ogg", "m4a", "wma"].includes(
      extension
    );
  };

  const isImageFile = (filename) => {
    const extension = filename.split(".").pop()?.toLowerCase();
    return ["jpg", "jpeg", "png", "gif", "bmp", "tiff"].includes(extension);
  };

  if (loading) {
    return (
      <div className="media-list">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading media files...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="media-list">
        <div className="error">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchMedia} className="retry-btn">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="media-list">
      <div className="list-header">
        <h2>Media Files in Container</h2>
        <button onClick={fetchMedia} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {videos.length === 0 &&
      audio.length === 0 &&
      images.length === 0 &&
      results.length === 0 &&
      temp.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📁</div>
          <p>No media files found in container</p>
          <span>Upload a video, audio, or image file to get started</span>
        </div>
      ) : (
        <div className="media-sections">
          {videos.length > 0 && (
            <div className="media-section">
              <h3>📤 Uploaded Videos ({videos.length})</h3>
              <div className="media-grid">
                {videos.map((video, index) => (
                  <div key={index} className="media-item">
                    <div className="media-info">
                      <div className="media-icon">{getFileIcon(video)}</div>
                      <div className="media-details">
                        <div className="media-name" title={video}>
                          {video}
                        </div>
                        <div className="media-meta">
                          <span className="media-type">
                            {video.split(".").pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="media-actions">
                      <button
                        onClick={() => handlePreview(video, "medias")}
                        className="preview-btn"
                        title="Preview video"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(video, "medias")}
                        disabled={downloading[video]}
                        className="download-btn"
                        title="Download video"
                      >
                        {downloading[video] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(video, "medias")}
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
            <div className="media-section">
              <h3>🎵 Uploaded Audio ({audio.length})</h3>
              <div className="media-grid">
                {audio.map((audioFile, index) => (
                  <div key={index} className="media-item">
                    <div className="media-info">
                      <div className="media-icon">{getFileIcon(audioFile)}</div>
                      <div className="media-details">
                        <div className="media-name" title={audioFile}>
                          {audioFile}
                        </div>
                        <div className="media-meta">
                          <span className="media-type">
                            {audioFile.split(".").pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="media-actions">
                      <button
                        onClick={() => handlePreview(audioFile, "medias")}
                        className="preview-btn"
                        title="Preview audio"
                      >
                        ▶️
                      </button>
                      <button
                        onClick={() => handleDownload(audioFile, "medias")}
                        disabled={downloading[audioFile]}
                        className="download-btn"
                        title="Download audio"
                      >
                        {downloading[audioFile] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(audioFile, "medias")}
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

          {images.length > 0 && (
            <div className="media-section">
              <h3>🖼️ Uploaded Images ({images.length})</h3>
              <div className="media-grid">
                {images.map((image, index) => (
                  <div key={index} className="media-item">
                    <div className="media-info">
                      <div className="media-icon">{getFileIcon(image)}</div>
                      <div className="media-details">
                        <div className="media-name" title={image}>
                          {image}
                        </div>
                        <div className="media-meta">
                          <span className="media-type">
                            {image.split(".").pop().toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="media-actions">
                      <button
                        onClick={() => handlePreview(image, "medias")}
                        className="preview-btn"
                        title="Preview image"
                      >
                        👁️
                      </button>
                      <button
                        onClick={() => handleDownload(image, "medias")}
                        disabled={downloading[image]}
                        className="download-btn"
                        title="Download image"
                      >
                        {downloading[image] ? "⏳" : "⬇️"}
                      </button>
                      <button
                        onClick={() => handleDelete(image, "medias")}
                        disabled={deleting[image]}
                        className="delete-btn"
                        title="Delete image"
                      >
                        {deleting[image] ? "⏳" : "🗑️"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div className="media-section">
              <h3>📥 Processed Results ({results.length})</h3>
              <div className="media-grid">
                {results.map((result, index) => (
                  <div key={index} className="media-item result-item">
                    <div className="media-info">
                      <div className="media-icon">{getFileIcon(result)}</div>
                      <div className="media-details">
                        <div className="media-name" title={result}>
                          {result}
                        </div>
                        <div className="media-meta">
                          <span className="media-type">
                            {result.split(".").pop().toUpperCase()}
                          </span>
                          <span className="result-badge">Processed</span>
                        </div>
                      </div>
                    </div>
                    <div className="media-actions">
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
            <div className="media-section">
              <h3>🗂️ Temporary Files ({temp.length})</h3>
              <div className="media-grid">
                {temp.map((tempFile, index) => (
                  <div key={index} className="media-item temp-item">
                    <div className="media-info">
                      <div className="media-icon">{getFileIcon(tempFile)}</div>
                      <div className="media-details">
                        <div className="media-name" title={tempFile}>
                          {tempFile}
                        </div>
                        <div className="media-meta">
                          <span className="media-type">
                            {tempFile.split(".").pop().toUpperCase()}
                          </span>
                          <span className="temp-badge">Temporary</span>
                        </div>
                      </div>
                    </div>
                    <div className="media-actions">
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
        <div className="media-preview-modal" onClick={closePreview}>
          <div
            className="media-preview-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="media-preview-header">
              <h3>{previewMedia.filename}</h3>
              <button className="close-btn" onClick={closePreview}>
                ✕
              </button>
            </div>
            <div className="media-preview-player">
              {isAudioFile(previewMedia.filename) ? (
                <audio
                  controls
                  autoPlay
                  src={previewMedia.url}
                  style={{ width: "100%" }}
                >
                  Your browser does not support the audio tag.
                </audio>
              ) : isImageFile(previewMedia.filename) ? (
                <img
                  src={previewMedia.url}
                  alt={previewMedia.filename}
                  style={{
                    maxWidth: "100%",
                    maxHeight: "80vh",
                    objectFit: "contain",
                  }}
                />
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
            <div className="media-preview-actions">
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

export default MediaList;
