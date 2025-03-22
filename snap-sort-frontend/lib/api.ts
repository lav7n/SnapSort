const API_URL = "/api";

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  
  const url = `${API_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      "Content-Type": "application/json",
    },
  });
  

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    // throw new Error(error.error || "An error occurred");
  }

  return response.json();
}

export async function registerUser(userData: Record<string, any>) {
  return fetchAPI("/auth/register", {
    method: "POST",
    body: JSON.stringify(userData),
  });
}



export async function logoutUser() {
  const response = await fetchAPI("/auth/logout", { method: "POST" });
  console.log(response)
  if (!response.ok) {
    throw new Error("Logout failed");
  }

  return response;
}





export async function loginUser(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);
  try {
    console.log("getting login work done");
    const response = await fetchAPI("/auth/login", {
      method: "POST",
      body: formData,
      credentials: "include", // Required for cookies
    });
    return response;
    

  } catch (err) {
    console.error("Error :", err);
    return null;
  }
  
}

export async function getSession() {
  try {
    const response = await fetchAPI("/auth/me", {
      method: "GET",
      credentials: "include",
    });

    if (response.error) {
      console.log(response.error);
      return null;
    }
    return response;
  } catch (err) {
    console.log(err)
    return null;
  }
}







export async function fetchEvents() {
  try {
      console.log("Fetching events...");

      const response = await fetchAPI("/events/list", {
          method: "GET",
          credentials: "include",
          headers: {
              "Accept": "application/json",
          },
      });

      if (response.error) {
          return { success: false, error: response.error };
      }
      return response;
  } catch (err) {
      console.error("Error fetching events:", err);
      return { success: false, error: "Internal Server Error" };
  }
}

export async function getEventById(eventId: string) {
  try {
    const response = await fetchAPI(`/events/${eventId}`, {
      method: "GET",
      credentials: "include",
      headers: {
        "Accept": "application/json",
      },
    });

    if (response.error) {
      return { success: false, error: response.error };
    }
    return { success: true, data: response };
  } catch (err) {
    console.error("Error fetching event details:", err);
    return { success: false, error: "Internal Server Error" };
  }
}

export async function joinEvent(eventCode:string) {
  try {
    console.log("Calling joinEvent...");

    const response = await fetchAPI("/events/join", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({ code: eventCode }),
    });

    if (response.error) {
      return { success: false, error: response.error };
    }
    return { success: true, message: response.message };
  } catch (err) {
    console.error("Error joining event:", err);
    return { success: false, error: "Internal Server Error" };
  }
}


export async function getEventImages(eventId: string) {
  return fetchAPI(`/events/${eventId}/images`);
}


export async function uploadEventImage(formData: FormData) {
  return fetchAPI(`/events/${formData.get("eventId")}/images`, {
    method: "POST",
    body: formData,
  });
}
