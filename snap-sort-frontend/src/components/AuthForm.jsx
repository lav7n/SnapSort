
import { useState, useContext } from "react";
import axios from "axios";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

const AuthForm = ({ type }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await axios.post("http://127.0.0.1:8000/login", {
        email,
        password,
      });

      const { access_token, user } = response.data;
      if (access_token && user) {
        login(access_token, user);
        console.log("Login successful:", user);
        window.location.href = "/dashboard"; // Redirect to dashboard
      } else {
        setErrorMessage("Invalid login response.");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Invalid email or password.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage("");

    try {
      await axios.post("http://127.0.0.1:8000/register", {
        email,
        password,
        fullName,
      });
      window.location.href = "/sign-in"; // Redirect to login after sign-up
    } catch (err) {
      console.error(err);
      setErrorMessage("Sign-up failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form
      onSubmit={type === "sign-in" ? handleLogin : handleSignUp}
      className="auth-form"
    >
      <h1 className="form-title">{type === "sign-in" ? "Sign In" : "Sign Up"}</h1>
      {type === "sign-up" && (
        <div className="shad-form-item">
          <label className="shad-form-label">Full Name</label>
          <Input
            type="text"
            placeholder="Enter your full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="shad-input"
            required
          />
        </div>
      )}

      <div className="shad-form-item">
        <label className="shad-form-label">Email</label>
        <Input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="shad-input"
          required
        />
      </div>

      <div className="shad-form-item">
        <label className="shad-form-label">Password</label>
        <Input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="shad-input"
          required
        />
      </div>

      {errorMessage && <p className="error-message">*{errorMessage}</p>}

      <Button type="submit" className="form-submit-button" disabled={isLoading}>
        {type === "sign-in" ? "Sign In" : "Sign Up"}
        {isLoading && <span className="ml-2 animate-spin">⏳</span>}
      </Button>

      {/* <div className="body-2 flex justify-center">
        <p className="text-light-100">
          {type === "sign-in"
            ? "Don't have an account?"
            : "Already have an account?"}
        </p>
        <Link
          href={type === "sign-in" ? "/sign-up" : "/sign-in"}
          className="ml-1 font-medium text-brand"
        >
          {type === "sign-in" ? "Sign Up" : "Sign In"}
        </Link>
      </div> */}
    </form>
  );
};

export default AuthForm;
