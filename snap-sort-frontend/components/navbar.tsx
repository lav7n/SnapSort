"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { UserNav } from "@/components/user-nav";
import { JoinEventModal } from "@/components/join-event-modal";
import { getSession } from "@/lib/api";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation"; // Use "next/navigation" instead of "next/router"

export function Navbar() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const sessionData = await getSession();
        if (sessionData) {
          setSession(sessionData);
        } else {
          router.push("/login");
        }
      } catch (error) {
        console.error("Error fetching session:", error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    fetchSession();
  }, [router]);

  if (loading) return null; // Prevent rendering while session is being fetched

  return (
    <header className="border-b">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold">EventShare</span>
        </Link>

        <nav className="flex items-center gap-4">
          {session ? (
            <>
              <UserNav user={session.user} />
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link href="/register">
                <Button>Register</Button>
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
