import { NextRequest, NextResponse } from "next/server";


export async function GET(req: NextRequest) {
    const token = req.cookies.get("auth_token");

    if (!token) {
        console.error("No token found");
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const fetchOptions: RequestInit = {
            method: "GET",
            credentials: "include",
            headers: {
                "Accept": "application/json",
                "Authorization": `Bearer ${token.value}`,
            },
        };

        const response = await fetch("http://localhost:8000/events/list", fetchOptions);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            return NextResponse.json({ error: error.detail || "Failed to fetch events" }, { status: response.status });
        }

        const responseData = await response.json();
        return NextResponse.json({ success: true, events: responseData }, { status: 200 });
    } catch (error) {
        console.error("Fetch error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}