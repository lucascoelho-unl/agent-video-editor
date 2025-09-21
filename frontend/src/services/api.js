// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8002/api/v1';

// HTTP status codes
const HTTP_STATUS = {
  OK: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
};

// Error messages
const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UPLOAD_FAILED: 'Upload failed. Please try again.',
  FETCH_VIDEOS_FAILED: 'Failed to fetch videos.',
  DELETE_FAILED: 'Failed to delete video.',
  CONTAINER_STATUS_FAILED: 'Failed to get container status.',
};

class ApiService {
  async _handleResponse(response) {
    if (!response.ok) {
      let errorMessage = ERROR_MESSAGES.NETWORK_ERROR;

      try {
        const error = await response.json();
        errorMessage = error.detail || errorMessage;
      } catch {
        // If response is not JSON, use status-based message
        switch (response.status) {
          case HTTP_STATUS.BAD_REQUEST:
            errorMessage = 'Invalid request. Please check your input.';
            break;
          case HTTP_STATUS.NOT_FOUND:
            errorMessage = 'Resource not found.';
            break;
          case HTTP_STATUS.SERVICE_UNAVAILABLE:
            errorMessage = 'Service temporarily unavailable.';
            break;
          case HTTP_STATUS.INTERNAL_SERVER_ERROR:
            errorMessage = 'Server error. Please try again later.';
            break;
        }
      }

      throw new Error(errorMessage);
    }

    return response.json();
  }

  async uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    return this._handleResponse(response);
  }

  async getVideos() {
    const response = await fetch(`${API_BASE_URL}/videos`);
    return this._handleResponse(response);
  }

  async deleteVideo(filename, source = 'videos') {
    const response = await fetch(
      `${API_BASE_URL}/videos/${filename}?source=${source}`,
      {
        method: 'DELETE',
      }
    );

    return this._handleResponse(response);
  }

  async getContainerStatus() {
    const response = await fetch(`${API_BASE_URL}/container/status`);
    return this._handleResponse(response);
  }

  getDownloadUrl(filename, source = 'results') {
    return `${API_BASE_URL}/download/${filename}?source=${source}`;
  }

  async downloadVideo(filename, source = 'results') {
    const response = await fetch(this.getDownloadUrl(filename, source));
    if (!response.ok) {
      throw new Error('Failed to download video');
    }
    return response.blob();
  }
}

export default new ApiService();
