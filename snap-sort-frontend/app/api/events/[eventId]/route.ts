import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: { eventId: string } }) {
    try {
        // Extract token safely
        const token = req.cookies.get("auth_token")?.value;
        if (!token) {
            console.error("No token found");
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        // Extract eventId safely
         const { eventId } = await params;
        if (!eventId) {
            return NextResponse.json({ error: "Event ID is required" }, { status: 400 });
        }

        const fetchOptions: RequestInit = {
            method: "GET",
            credentials: "include",
            headers: {
                "Accept": "application/json",
                "Authorization": `Bearer ${token}`,
            },
        };

        const response = await fetch(`http://localhost:8000/events/${eventId}`, fetchOptions);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            return NextResponse.json({ error: error.detail || "Failed to fetch event" }, { status: response.status });
        }

        const eventData = await response.json();
        return NextResponse.json({ success: true, data: eventData }, { status: 200 });

    } catch (error) {
        console.error("Fetch error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
