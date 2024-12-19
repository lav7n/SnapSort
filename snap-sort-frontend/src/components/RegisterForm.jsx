// components/RegisterForm.js
import React, { useState } from "react";

const RegisterForm = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [imageBase64, setImageBase64] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!imageBase64) {
      alert("Please upload an image.");
      return;
    }

    const userData = {
      name,
      email,
      password,
      image: imageBase64,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("User registered successfully:", data);
      } else {
        console.error("Failed to register user.");
      }
    } catch (error) {
      console.error("Error during registration:", error);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageBase64(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <form onSubmit={handleRegister} className="form">
      <h2>Register</h2>
      <label>Name</label>
      <input
        type="text"
        placeholder="Enter your name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
      />
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
      <label>Upload Your Face Image</label>
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        required
      />
      <button type="submit">Register</button>
    </form>
  );
};

export default RegisterForm;
