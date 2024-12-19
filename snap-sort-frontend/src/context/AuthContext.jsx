import React, { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (token) {
      const decodedUser = decodeToken(token);
      setUser(decodedUser);
    }
    
    setLoading(false);
  }, []);

  const login = (token, userInfo) => {
    localStorage.setItem("access_token", token);
    setUser(userInfo);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const decodeToken = (token) => {
  const decodedToken = jwtDecode(token);
  console.log(decodedToken);
  return decodedToken;
};
