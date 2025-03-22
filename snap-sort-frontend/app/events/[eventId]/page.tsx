"use client";
import { notFound, redirect, useParams, useRouter } from "next/navigation"
import Image from "next/image"
import { getEventById, getSession } from "@/lib/api"
import { useEffect, useState } from "react"



// Dummy data for event images
const dummyImages = [
  {
    id: "img1",
    url: "/placeholder.svg?height=400&width=400&text=Group+Photo",
    userName: "John Smith",
  },
  {
    id: "img2",
    url: "/placeholder.svg?height=400&width=400&text=Dance+Floor",
    userName: "Emily Johnson",
  },
  {
    id: "img3",
    url: "/placeholder.svg?height=400&width=400&text=Food+Table",
    userName: "Michael Brown",
  },
  {
    id: "img4",
    url: "/placeholder.svg?height=400&width=400&text=Awards+Ceremony",
    userName: "Sarah Davis",
  },
  {
    id: "img5",
    url: "/placeholder.svg?height=400&width=400&text=Team+Photo",
    userName: "David Wilson",
  },
  {
    id: "img6",
    url: "/placeholder.svg?height=400&width=400&text=DJ+Booth",
    userName: "Jessica Martinez",
  },
]


export default function EventPage() {
  const router = useRouter()
  const params = useParams();
  const eventId = Array.isArray(params.eventId) ? params.eventId[0] : params.eventId ?? "defaultEventId";
  const [loading, setLoading] = useState(true);
  const [event, setEvent] = useState(null);
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const sessionData = await getSession();
        if (!sessionData) {
          router.push("/login");  // Redirect to login if no session
        } else {
          const response = await getEventById(eventId);
          setEvent(response.data.data);
          if (!event) {
            notFound()
          }
        }
      } catch (error) {
        console.error("Error fetching session:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSession(); // Call the async function
  }, [router]);
  const images = dummyImages
  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{event?.name}</h1>
        <p className="text-muted-foreground">{event?.description}</p>
      </div>


      <h2 className="text-2xl font-semibold mb-4">Event Images</h2>

      {images.length === 0 ? (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground">No images have been uploaded to this event yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {images.map((image) => (
            <div key={image.id} className="border rounded-lg overflow-hidden">
              <div className="relative aspect-square">
                <Image src={image.url || "/placeholder.svg"} alt="Event image" fill className="object-cover" />
              </div>
              <div className="p-3">
                <p className="text-sm text-muted-foreground">Uploaded by {image.userName}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

