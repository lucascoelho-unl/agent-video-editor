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
  const [uploadQueue, setUploadQueue] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});

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

  const validateFiles = (files) => {
    const validFiles = [];
    const errors = [];

    Array.from(files).forEach((file, index) => {
      try {
        validateFile(file);
        validFiles.push(file);
      } catch (error) {
        errors.push(`${file.name}: ${error.message}`);
      }
    });

    if (errors.length > 0) {
      throw new Error(`Validation errors:\n${errors.join('\n')}`);
    }

    return validFiles;
  };

  const handleUpload = async (files) => {
    try {
      const validFiles = validateFiles(files);

      if (validFiles.length === 0) {
        throw new Error('No valid files to upload.');
      }

      setIsUploading(true);
      setUploadQueue(validFiles);
      setUploadProgress({});

      const results = [];
      const errors = [];

      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        try {
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { status: 'uploading', progress: 0 }
          }));

          const result = await apiService.uploadVideo(file);
          results.push(result);

          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { status: 'completed', progress: 100 }
          }));

        } catch (error) {
          errors.push(`${file.name}: ${error.message}`);
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { status: 'error', progress: 0 }
          }));
        }
      }

      setIsUploading(false);
      setUploadQueue([]);

      if (results.length > 0) {
        onUploadSuccess?.({
          message: `Successfully uploaded ${results.length} file(s)`,
          results,
          errors: errors.length > 0 ? errors : undefined
        });
      }

      if (errors.length > 0) {
        onUploadError?.(errors.join('\n'));
      }

    } catch (error) {
      setIsUploading(false);
      setUploadQueue([]);
      setUploadProgress({});
      onUploadError?.(error.message);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleUpload(files);
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
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleUpload(files);
    }
    // Reset the input value so the same file can be selected again
    e.target.value = '';
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
            <p>Uploading {uploadQueue.length} video(s)...</p>
            {uploadQueue.length > 0 && (
              <div className="upload-queue">
                {uploadQueue.map((file, index) => (
                  <div key={index} className="upload-item">
                    <span className="file-name">{file.name}</span>
                    <span className={`upload-status ${uploadProgress[file.name]?.status || 'pending'}`}>
                      {uploadProgress[file.name]?.status === 'uploading' && '⏳'}
                      {uploadProgress[file.name]?.status === 'completed' && '✅'}
                      {uploadProgress[file.name]?.status === 'error' && '❌'}
                      {!uploadProgress[file.name] && '⏸️'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10,9 9,9 8,9" />
              </svg>
            </div>
            <h3>Upload Videos</h3>
            <p>Drag and drop your videos here, or click to browse</p>
            <div className="file-types">
              <span>Supported: {SUPPORTED_FORMATS}</span>
            </div>
            <div className="multiple-files-hint">
              <span>📁 Multiple files supported</span>
            </div>
            <input
              type="file"
              accept="video/*"
              multiple
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
