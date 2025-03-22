import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    const token = req.cookies.get("auth_token");

    if (!token) {
        console.error("No token found");
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const { code } = await req.json(); // Extract event code from request body

        const fetchOptions: RequestInit = {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": `Bearer ${token.value}`,
            },
            body: JSON.stringify({ code })
        };

        const response = await fetch("http://localhost:8000/events/join", fetchOptions);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            return NextResponse.json({ error: error.detail || "Failed to join event" }, { status: response.status });
        }

        const responseData = await response.json();
        return NextResponse.json({ success: true, message: responseData.message }, { status: 200 });
    } catch (error) {
        console.error("Fetch error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
