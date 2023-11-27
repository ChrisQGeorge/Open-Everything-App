import { useEffect, useState } from 'react';
import checkAuth from "../components/checkAuth"
import { useRouter } from 'next/router';

export default function Home() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
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
          }
      }
  }, [status, loading, router]);

  if(!loading){
    return (
      <div>
        <p>Loaded Dashboard!!!</p>
      </div>
    )
  }else{
    return (
      <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
          <p> {!loading ? message : "Loading.."}</p>
      </div>
    )
  }

}