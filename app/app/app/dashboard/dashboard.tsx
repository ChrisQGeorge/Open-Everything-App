"use client"
import { useEffect, useState } from 'react';
import checkAuth from "../../components/checkAuth"
import { useRouter } from 'next/navigation';
import Cookie from 'js-cookie';

const blankUser = {
  'username':"",
  'email':"",
  'profile_image':"",
  'attributes':[""],
  'roles':[""],
  'settings':[""]
}

export default function Dashboard() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [render, renderPage] = useState(false);
  const [user, setUser] = useState(blankUser)
  const [attributes, setAttributes] = useState([])
  const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
  const router = useRouter(); // Initialize useRouter
  const token = Cookie.get("token") || null

  useEffect(() => {
      const getData = async () => {
          const res = await checkAuth();
          setMessage(res.message || '');
          setLoading(false);
          setStatus(res.status);
          setUser(res.data)
          console.log(res.data)
          console.log(res.data.attributes)

          if(res.data.attributes){
            setAttributes(res.data.attributes)
          }
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

  const getData = async (event: { preventDefault: () => void; }) => {

    const response = await fetch('/api/get/weight', {
        headers: {
          'Authorization': `Bearer ${token}`
        },

        method: "POST",
    });
    console.log(response)
  

  

};



  if(render){
    return (
      <div className="text-black items-center justify-center min-h-screen bg-gradient-to-tl from-pink-300 via-purple-300 to-indigo-400 h-screen flex items-center justify-center">
        <div className="rounded-xl w-11/12 h-5/6 bg-gray-200 bg-opacity-80 overflow-y-auto p-10">
          <p>Loaded Dashboard!!! Your username is {user.username}</p>
          <ul>
            {attributes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <button className="px-6 py-2 mt-4 text-black bg-white rounded-lg hover:bg-blue-900 w-auto"
              type="submit"
              onClick={getData}
              >getData</button>
          <button 
              className="px-6 py-2 mt-4 text-black bg-white rounded-lg hover:bg-blue-900 w-auto"
              type="submit"
              onClick={logout}
          >Logout</button>
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