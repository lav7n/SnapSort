import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {

  const token = req.cookies.get("auth_token"); // Adjust based on where you're storing the token

  if (!token) {
      console.error("No token found");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
      const fetchOptions: RequestInit = {
          method: "GET",
          credentials: "include",
          headers: {
              "Content-Type": "application/json",
              "Accept": "application/json",
              "Authorization": `Bearer ${token.value}`, // Include token in Authorization header
          },
      };


      const response = await fetch("http://localhost:8000/auth/me", fetchOptions);

      if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          return NextResponse.json({ error: error.detail || "Failed to fetch user" }, { status: response.status });
      }

      const userData = await response.json();


      return NextResponse.json({ success: true, user: userData }, { status: 200 });
  } catch (error) {
      console.error("Fetch error:", error);
      return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
