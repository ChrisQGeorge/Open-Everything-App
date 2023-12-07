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

interface AttributeData {
  attr_name: string;
  data_array: any[]; // Replace 'any' with a more specific type if possible
  id: string; // Assuming each item has an 'id' for the key prop
}

export default function Dashboard() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [render, renderPage] = useState(false);
  const [user, setUser] = useState(blankUser)
  const [attributes, setAttributes] = useState([])
  const [attrArray, setAttrArray] = useState<AttributeData[]>([]);
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

          if(res.data.attributes){
            setAttributes(res.data.attributes)
            loadAttributes()
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

  /*const getData = async (attribute: string) => {

    const response = await  fetch('/api/get/'+attribute, {
        headers: {
          'Authorization': `Bearer ${token}`
        },

        method: "GET",
    });

    if(response.ok){
      const data = await response.json()
      if(data.data_array){
        return {attribute: data.data_array}
      } else {
        return {attribute: null}
      }


    }*/
  
const loadAttributes = async () => {
    const queryParams = new URLSearchParams();
    for (let attribute of attributes) {
        queryParams.append('a', attribute);
    }

    console.log(queryParams.toString());

    const response = await fetch('/api/getMany?' + queryParams.toString(), {
        headers: {
            'Authorization': `Bearer ${token}`
        },
        method: "GET",
    });

    if (response.ok) {
        const data = await response.json();
        if (data.data) {
            setAttrArray(data.data);
        }
        console.log(attrArray)
    }
};



  if(render){
    return (
      <div className="text-black items-center justify-center min-h-screen bg-gradient-to-tl from-pink-300 via-purple-300 to-indigo-400 h-screen flex items-center justify-center">
        <div className="rounded-xl w-11/12 h-5/6 bg-gray-200 bg-opacity-80 overflow-y-auto p-10">
          <p>Loaded Dashboard!!! Your username is {user.username}</p>
          <h1>Attributes</h1>

          <ul>
            {attrArray.map((dataArray) => (
                    <li key={dataArray.attr_name}>
                      Name: {dataArray.attr_name} 
                      Data: {dataArray.data_array.length > 0 ? JSON.stringify(dataArray.data_array[dataArray.data_array.length - 1]) : 'No data'}
                    </li>
                ))}
          </ul>
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