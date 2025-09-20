import React, { useEffect } from 'react';
import './Notification.css';

const Notification = ({ message, type = 'info', onClose, duration = 5000 }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <div className={`notification ${type}`}>
      <div className="notification-content">
        <div className="notification-icon">
          {type === 'success' && '✅'}
          {type === 'error' && '❌'}
          {type === 'warning' && '⚠️'}
          {type === 'info' && 'ℹ️'}
        </div>
        <div className="notification-message">
          {message}
        </div>
        <button onClick={onClose} className="notification-close">
          ×
        </button>
      </div>
    </div>
  );
};

export default Notification;
