"use client"
import { useEffect, useState, createContext} from 'react';
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

const Dashboard = () =>  {
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
    }
};



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