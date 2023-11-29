import { useEffect, useState } from 'react';
import { useRouter } from 'next/router'; // Import useRouter
import checkAuth from "../components/checkAuth"

export default function Home() {
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
                router.push('/login');
            } else if (status === 399) {
                router.push('/setup');
            } else if (status === 398) {
                router.push('/rebuild');
            } else if (status >= 200 && status < 300) {
                router.push('/dashboard');
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
