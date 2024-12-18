// components/LoginForm.js
import React, { useState } from "react";
import axios from "axios";

const LoginForm = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // Sending POST request to the FastAPI backend
      const response = await axios.post("http://localhost:8000/login", {
        email,
        password,
      });

      // On success, store the JWT token in localStorage
      const { access_token } = response.data;
      localStorage.setItem("access_token", access_token);  // Store token in localStorage

      console.log("Login successful:", response.data);
      // Redirect user to dashboard or another page on successful login
      // Example: window.location.href = "/dashboard";
    } catch (err) {
      setError("Invalid email or password.");
    }
  };

  return (
    <form onSubmit={handleLogin} className="form">
      <h2>Login</h2>
      <label>Email</label>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <label>Password</label>
      <input
        type="password"
        placeholder="Enter your password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit">Login</button>
    </form>
  );
};

export default LoginForm;
