"use client"
import { useEffect, useState, createContext} from 'react';
import checkAuth from "../../components/checkAuth"
import { useRouter } from 'next/navigation';
import Cookie from 'js-cookie';

const Dashboard = () =>  {
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
      <div className="text-black items-center justify-center min-h-screen bg-gradient-to-tl from-pink-300 via-purple-300 to-indigo-400 h-screen flex items-center justify-center">
        <div className="rounded-xl w-11/12 h-5/6 bg-gray-200 bg-opacity-50 p-7 inline-block">
          <div className="w-1/3 h-full m-0 float-left">
            <div className="h-1/3 w-full m-0">
              <CatNav />
            </div>
            <div className="h-1/3 w-full m-0">
              <div className="h-fit w-full rounded-xl bg-gray-200 bg-opacity-80 m-4" >

                <p>Test Pane2</p>

              </div>
            </div>
          </div>
          <div className="w-2/3 h-full m-0 float-left">
            <button 
                className="px-6 py-2 mt-4 text-black bg-white rounded-lg hover:bg-blue-900 w-auto"
                type="submit"
                onClick={logout}
            >Logout</button>
          </div>
        </div>
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

function CatNav(){
  return (
      <div className="h-fit w-full rounded-xl bg-gray-200 bg-opacity-80 m-4" >

          <p>Test Pane</p>

      </div>
  )

}

export default Dashboard;