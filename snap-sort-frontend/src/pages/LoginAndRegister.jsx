
import React, { useState } from "react";
import AuthForm from "../components/AuthForm";

const LoginAndRegister = () => {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="login-register-container">
      <div className="form-toggle">
        <button
          className={isLogin ? "active" : ""}
          onClick={() => setIsLogin(true)}
        >
          Login
        </button>
        <button
          className={!isLogin ? "active" : ""}
          onClick={() => setIsLogin(false)}
        >
          Register
        </button>
      </div>

      {isLogin ? <AuthForm type="sign-up" /> : <AuthForm type="sign-in" />}
    </div>
  );
};

export default LoginAndRegister;
