import React, { useState } from "react";
import MediaUpload from "./components/MediaUpload";
import MediaList from "./components/MediaList";
import ContainerStatus from "./components/ContainerStatus";
import Notification from "./components/Notification";
import ErrorBoundary from "./components/ErrorBoundary";
import "./App.css";

function App() {
  const [notifications, setNotifications] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const addNotification = (message, type = "info") => {
    const id = Date.now();
    setNotifications((prev) => [...prev, { id, message, type }]);
  };

  const removeNotification = (id) => {
    setNotifications((prev) =>
      prev.filter((notification) => notification.id !== id)
    );
  };

  const handleUploadSuccess = (result) => {
    addNotification(result.message, "success");
    setRefreshTrigger((prev) => prev + 1);

    // If there were partial errors, show them as warnings
    if (result.errors && result.errors.length > 0) {
      addNotification(
        `Some files had issues: ${result.errors.join(", ")}`,
        "warning"
      );
    }
  };

  const handleUploadError = (error) => {
    addNotification(error, "error");
  };

  const handleDeleteSuccess = (message) => {
    addNotification(message, "success");
  };

  const handleDeleteError = (error) => {
    addNotification(error, "error");
  };

  return (
    <ErrorBoundary>
      <div className="App">
        <header className="app-header">
          <div className="header-content">
            <h1>Media Editor Agent</h1>
            <p>Upload and manage media in your Docker container</p>
          </div>
        </header>

        <main className="app-main">
          <div className="container">
            <ContainerStatus />

            <section className="upload-section">
              <MediaUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </section>

            <section className="media-section">
              <MediaList
                refreshTrigger={refreshTrigger}
                onDeleteSuccess={handleDeleteSuccess}
                onDeleteError={handleDeleteError}
              />
            </section>
          </div>
        </main>
        {/* Notifications */}
        {notifications.map((notification) => (
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
