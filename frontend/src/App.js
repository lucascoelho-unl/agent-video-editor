import React, { useState } from 'react';
import VideoUpload from './components/VideoUpload';
import VideoList from './components/VideoList';
import ContainerStatus from './components/ContainerStatus';
import Notification from './components/Notification';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  const [notifications, setNotifications] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const handleUploadSuccess = (result) => {
    addNotification(result.message, 'success');
    setRefreshTrigger(prev => prev + 1);
  };

  const handleUploadError = (error) => {
    addNotification(error, 'error');
  };

  const handleDeleteSuccess = (message) => {
    addNotification(message, 'success');
  };

  const handleDeleteError = (error) => {
    addNotification(error, 'error');
  };

  return (
    <ErrorBoundary>
      <div className="App">
        <header className="app-header">
          <div className="header-content">
            <h1>Video Editor Agent</h1>
            <p>Upload and manage videos in your Docker container</p>
          </div>
        </header>

        <main className="app-main">
          <div className="container">
            <ContainerStatus />
            
            <section className="upload-section">
              <VideoUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </section>

            <section className="videos-section">
              <VideoList
                refreshTrigger={refreshTrigger}
                onDeleteSuccess={handleDeleteSuccess}
                onDeleteError={handleDeleteError}
              />
            </section>
          </div>
        </main>

        <footer className="app-footer">
          <p>Built with React & FastAPI</p>
        </footer>

        {/* Notifications */}
        {notifications.map(notification => (
          <Notification
            key={notification.id}
            message={notification.message}
            type={notification.type}
            onClose={() => removeNotification(notification.id)}
          />
        ))}
      </div>
    </ErrorBoundary>
  );
}

export default App;