"use client"
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter
import checkAuth from "../../components/checkAuth"

export default function Index() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [render, renderPage] = useState(false);
    const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
    const router = useRouter(); // Initialize useRouter

    useEffect(() => {
        const getData = async () => {
            const res = await checkAuth();
            setMessage(res.message || '');
            setLoading(false)
            setStatus(res.status)
        }
        getData()
    }, [status])

    useEffect(() => {
        if (!loading) {
            if (status >= 400 && status < 600) {
                router.push('/auth/login');
            } else if (status === 399) {
                router.push('/auth/setup');
            } else if (status === 398) {
                router.push('/auth/rebuild');
            } else if (status >= 200 && status < 300) {
                router.push('/app/dashboard');
            }
            renderPage(true)
        }
    }, [status, loading, router]);

    
  return (
    <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
        <p> {!render ? message : "Loading.."}</p>
    </div>
  )
}
