import React, { useState, useCallback } from 'react';
import apiService from '../services/api';
import './VideoUpload.css';

// Constants
const ALLOWED_TYPES = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
const SUPPORTED_FORMATS = 'MP4, AVI, MOV, MKV, WebM';

const VideoUpload = ({ onUploadSuccess, onUploadError }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const validateFile = (file) => {
    if (!file) {
      throw new Error('No file selected.');
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      throw new Error(`Unsupported file type. Please upload ${SUPPORTED_FORMATS} files.`);
    }
    
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`File size too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB.`);
    }
  };

  const handleUpload = async (file) => {
    try {
      validateFile(file);
      setIsUploading(true);

      const result = await apiService.uploadVideo(file);
      
      setIsUploading(false);
      onUploadSuccess?.(result);

    } catch (error) {
      setIsUploading(false);
      onUploadError?.(error.message);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleUpload(file);
    }
  };

  return (
    <div className="video-upload">
      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isUploading ? (
          <div className="upload-progress">
            <div className="loading-spinner"></div>
            <p>Uploading video...</p>
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
            </div>
            <h3>Upload Video</h3>
            <p>Drag and drop your video here, or click to browse</p>
            <div className="file-types">
              <span>Supported: {SUPPORTED_FORMATS}</span>
            </div>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="file-input"
              disabled={isUploading}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoUpload;
