// components/LoginForm.js
import React, { useState } from "react";
import axios from "axios";
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';


const LoginForm = () => {
  const { login } = useContext(AuthContext); 
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post('http://127.0.0.1:8000/login', {
        email,
        password,
      });

      const { access_token, user } = response.data;
      if (access_token && user) {
        login(access_token, user);  // Call the login function from AuthContext
        console.log('Login successful:', user);
        window.location.href = '/dashboard'; // Redirect to dashboard
      } else {
        setError('Invalid login response.');
      }
    } catch (err) {
      console.error(err);
      setError('Invalid email or password.');
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
