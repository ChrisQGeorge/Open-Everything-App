"use client"
import { useEffect, useState } from 'react';
import checkAuth from "../../../components/checkAuth"
import { useRouter } from 'next/navigation';
import Cookie from 'js-cookie';

export default function Dashboard() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [render, renderPage] = useState(false);
  const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
  const router = useRouter(); // Initialize useRouter

  useEffect(() => {
      const getData = async () => {
          const res = await checkAuth();
          setMessage(res.message || '');
          setLoading(false);
          setStatus(res.status);
      }
      getData();
  }, [status]);

  useEffect(() => {
      if (!loading) {
          if (status >= 400 && status < 600) {
              router.push('/auth/login');
          } else if (status === 399) {
              router.push('/auth/setup');
          } else if (status === 398) {
              router.push('/auth/rebuild');
          }
          renderPage(true);
      }
  }, [status, loading, router]);
  


  const logout = (() => {
    Cookie.remove('token');
    router.push("/")
  });



  if(render){
    return (
      <div>
        <p>Loaded Dashboard!!!</p>

        <button 
            className="px-6 py-2 mt-4 text-black bg-white rounded-lg hover:bg-blue-900 w-auto"
            type="submit"
            onClick={logout}
        >Logout</button>
      </div>
    )
  }else{
    return (
      <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
          <p> {!render ? message : "Loading.."}</p>
      </div>
    )
  }

}