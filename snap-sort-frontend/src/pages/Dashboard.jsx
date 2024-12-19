// src/components/Dashboard.js
import React from "react";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const navigate = useNavigate();
  const user = {
    username: "JohnDoe",
    email: "johndoe@example.com",
    role: "User",
  };

  return (
    <div className="dashboard">
      <h1>Welcome to Your Dashboard</h1>
      
      <div className="user-info">
        <h2>User Information</h2>
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role}</p>
      </div>

      <div className="actions">
        <h2>Actions</h2>
        <button onClick={() => navigate("/profile")}>Go to Profile</button>
        <button onClick={() => navigate("/settings")}>Go to Settings</button>
      </div>
    </div>
  );
};

export default Dashboard;
