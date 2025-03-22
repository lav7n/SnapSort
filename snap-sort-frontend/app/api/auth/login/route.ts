import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    // Parse request body
    const bodyText = await req.text();
    const formBody = new URLSearchParams(bodyText);

    const response = await fetch("http://localhost:8000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formBody,
      credentials: "include", 
    });


    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json({ error: error.detail || "Login failed" }, { status: response.status });
    }

    const cookies = response.headers.get("set-cookie");
    const res = NextResponse.json({ success: true }, { status: 200 });

    if (cookies) {
      res.headers.set("Set-Cookie", cookies);
    }

    return res;
  } catch (error) {
    console.error("❌ Login API Error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
