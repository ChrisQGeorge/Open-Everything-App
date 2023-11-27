import { useEffect, useState } from 'react';
import { useRouter } from 'next/router'; // Import useRouter
import Cookie from 'js-cookie';

export default function Home() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
    const router = useRouter(); // Initialize useRouter



    useEffect(() => {
      const token = Cookie.get('token');
      if (token) {
          fetch('/api/users/me/', {
              headers: {
                  'Authorization': `Bearer ${token}`
              }
          })
          .then(res => {
            const status = res.status;
            return res.json().then(data => ({
                status: status,
                data: data
            }))
          })
            .then(result=> {
              setLoading(false);
              setStatus(result.status)
          })
          .catch(error => {
              console.error('Error fetching data:', error);
              setLoading(false);
          });
      }
  }, [router]);


    useEffect(() => {
        if (!loading) {
            if (status >= 400 && status < 600) {
                router.push('/login');
            } else if (status >= 300 && status < 400) {
                router.push('/setup');
            } else if (status >= 200 && status < 300) {
                router.push('/dashboard');
            }
        }
    }, [status, loading, router]);
  return (
    <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
        <p> {!loading ? message : "Loading.."}</p>
    </div>
  )
}
