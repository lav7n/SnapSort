"use client";

import React, { useState, useRef } from "react";

const AuthForm = ({ type }) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [imageBase64, setImageBase64] = useState("");
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const openCamera = () => {
    setIsCameraOpen(true);
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch((error) => {
        console.error("Error accessing camera:", error);
      });
  };

  const captureImage = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (canvas && video) {
      const context = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert the image on the canvas to Base64
      const imageDataUrl = canvas.toDataURL("image/png");
      setImageBase64(imageDataUrl);

      // Stop the camera stream
      const stream = video.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach((track) => track.stop());
      setIsCameraOpen(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!imageBase64) {
      alert("Please capture an image.");
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
        window.location.href = "/sign-in"; // Redirect to login after registration
      } else {
        setErrorMessage("Failed to register user.");
      }
    } catch (error) {
      console.error("Error during registration:", error);
      setErrorMessage("Error occurred while registering. Please try again.");
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const { access_token, user } = await response.json();
        console.log("Login successful:", user);
        window.location.href = "/dashboard"; // Redirect to dashboard
      } else {
        setErrorMessage("Invalid email or password.");
      }
    } catch (err) {
      console.error("Error during login:", err);
      setErrorMessage("Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form
      onSubmit={type === "sign-in" ? handleLogin : handleRegister}
      className="auth-form"
    >
      <h1>{type === "sign-in" ? "Sign In" : "Register"}</h1>

      {type === "sign-up" && (
        <div className="form-group">
          <label>Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            required
          />
        </div>
      )}

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
        />
      </div>

      <div className="form-group">
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          required
        />
      </div>

      {type === "sign-up" && (
        <div className="form-group">
          <label>Capture Your Face Image</label>
          {!isCameraOpen ? (
            <button type="button" onClick={openCamera}>
              Open Camera
            </button>
          ) : (
            <div>
              <video ref={videoRef} autoPlay />
              <button type="button" onClick={captureImage}>
                Capture
              </button>
              <canvas ref={canvasRef} style={{ display: "none" }} />
            </div>
          )}
          {imageBase64 && (
            <div>
              <h3>Captured Image:</h3>
              <img src={imageBase64} alt="Captured" style={{ maxWidth: "100%" }} />
            </div>
          )}
        </div>
      )}

      {errorMessage && <p className="error">{errorMessage}</p>}

      <button type="submit" disabled={isLoading}>
        {type === "sign-in" ? "Sign In" : "Register"}
      </button>
    </form>
  );
};

export default AuthForm;
