"use client"
import { useEffect, useState, createContext, JSXElementConstructor, Key, PromiseLikeOfReactNode, ReactElement, ReactNode} from 'react';
import checkAuth from "../../components/checkAuth"
import { useRouter } from 'next/navigation';
import * as Unicons from '@iconscout/react-unicons';
import Cookie from 'js-cookie';

const blankUser = {
  'username':"",
  'email':"",
  'profile_image':"",
  'attributes':[""],
  'roles':[""],
  'settings':[""]
}

const sampleCatagories = [
  {category:"Health", icon:"UilHeart", color:"text-[#fcba03]"},
  {category:"Body", icon:"UilWeight",color:"text-[blue]"},
  {category:"Food",icon:"UilPizzaSlice",color:"text-[green]"},
  {category:"Fitness",icon:"UilDumbbell",color:"text-[violet]"},
  {category:"Productivity",icon:"UilClock",color:"text-[black]"},
]


const Dashboard = () =>  {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [render, renderPage] = useState(false);
  const [user, setUser] = useState(blankUser)
  const [attributes, setAttributes] = useState([])
  const [attrArray, setAttrArray] = useState<AttributeData[]>([]);
  const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
  const [currentCategory, setCategory] = useState("default");
  const [categories, setCategoryList] = useState(sampleCatagories);
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

  const createCategory = async () => {
    console.log("Create Attribute Button Pressed")
  }

  if(render){
    return (
      <div className="text-black items-center justify-center min-h-screen bg-gradient-to-tl from-pink-300 via-purple-300 to-indigo-400 h-screen flex items-center justify-center">
        <div className="rounded-xl w-11/12 h-5/6 bg-gray-200 bg-opacity-50 p-7">
          <div className="p-0 inline-block h-full w-full overflow-visible">
            <div className="w-[calc(33%-16px)] h-full mr-4 p-0 float-left box-border overflow-auto">
              <CatNav createCategory={createCategory} currCat={currentCategory} loadCat={setCategory} catList={categories}/>
              <PageNav />
              <button 
                  className="px-6 py-2 mt-4 text-black bg-white rounded-lg hover:bg-blue-900 w-auto"
                  type="submit"
                  onClick={logout}
              >Logout</button>
            </div>
            <div className="w-[67%] h-full overflow-auto m-0 float-left box-border">
              <AttributesTable attrs={attrArray}/>
            </div>
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


interface CategoryData {
  category:string;
  icon:string
  color:string
}

interface CatNavProps {
  catList:CategoryData[]
  currCat:string
  loadCat: (category: string) => void;
  createCategory: () => void;
}


const CatNav: React.FC<CatNavProps> = ({ catList, currCat, loadCat, createCategory }) => {
  var currentCategory = currCat

  const handleSelect = (category: string) => {
    loadCat(category)
  }

  return (
    <div className=" min-h-[33%] h-auto p-4 w-full mb-4 box-border rounded-xl bg-gray-200 bg-opacity-80 m-0">
      <table className="w-full">
        {catList.map((data: CategoryData) => {
          const IconComp = Unicons[data.icon];
          const trStyles = "rounded w-full font-semibold cursor-pointer " + ((currentCategory == data.category) ? "bg-gray-400 bg-opacity-40" : "")

          return(
            <tr id= {data.category} className={trStyles}  onClick ={() => handleSelect(data.category)}>
              <td className = {data.color}>
                <IconComp />
              </td>
              <td className="pl-4 text-lg">
                {data.category}
              </td>
            </tr>
          )
        })}
        <tr className="cursor-pointer font-semibold" onClick={() => createCategory()}>
          <td><Unicons.UilPlus /></td>
          <td className="pl-4">
            <button className="text-lg">Add More</button>
          </td>
        </tr>
      </table>
    </div>

  )
}

const PageNav = (props: any) => {

  const handleNav = (page: string) => {
    //router.push('/app/'+page)
  }
 
  return (
    <div className="min-h-[33%] p-4 w-full box-border box-border w-full rounded-xl bg-gray-200 m-0 bg-opacity-80">
      <table> 
        <tr>
          <td onClick = {() => handleNav("test")}>

          </td>
          <td>

          </td>
        </tr>

      </table>
    </div>

  )
}


interface AttributeData {
  attr_name: string;
  data_array: any[]; // Replace 'any' with a more specific type if possible
  id: string; // Assuming each item has an 'id' for the key prop
}

interface AttributesTableProps {
  attrs: AttributeData[];
}
const AttributesTable: React.FC<AttributesTableProps> = ({ attrs }) => {
  return (
  <div className="min-h-full h-auto rounded-xl bg-gray-200 bg-opacity-80 box-border p-4" >
    <table className="w-full p-0">
        {attrs.map((dataArray: AttributeData) => (
          <tr className="border-b-[10px] border-transparent"key={String(dataArray.attr_name)}>
            <td className="text-xl font-semibold float-left">
              {String(dataArray.attr_name)}
            </td>
            <td className="text-xl font-medium float-right">
              <input></input>{dataArray.data_array.length > 0 ? JSON.parse(dataArray.data_array[dataArray.data_array.length - 1].data) : 'Enter Value'}
            </td>
          </tr>
            ))}
    </table>
  </div>
  )

}

export default Dashboard;