import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import checkAuth from "../components/checkAuth"


export default function Setup() {
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [password, setPassword] = useState("")
    const [render, renderPage] = useState(false);
    const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
    const router = useRouter(); // Initialize useRouter
    const [errorMessage, setError] = useState('');

    useEffect(() => {
        const getData = async () => {
            const res = await checkAuth();
            setMessage(res.message || '');
            setLoading(false)
            setStatus(res.status)
        }
        getData()
    }, [loading])
  
    useEffect(() => {
        if (!loading) {
            if (status >= 400 && status < 600) {
                router.push('/login');
            } else if (status === 399) {
                router.push('/setup');
            } else if (status >= 200 && status < 300) {
                router.push('/dashboard');
            }
            renderPage(true)
        }
    }, [status, loading, router]);

    
    

    const handleSubmit = async (event: { preventDefault: () => void; }) => {
        event.preventDefault(); // Prevent the default form submission

        setLoading(true)

        event.preventDefault();
        const formData = new URLSearchParams();
        formData.append('password', password);

        const response = await fetch('/api/setup/rebuild', {
            body: formData,
            method: "POST",
        });

        if(response.ok){
            const data = await response.json();
            router.push('/login'); // Use router.push to navigate
            setLoading(false)

        } else {
            setError("Error: Failed to rebuild");
            setLoading(false)
        }
    };


    if(render){
        if (status == 398){
            return(
                <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
                    <div className="px-8 py-6 text-left bg-white shadow-lg">
                        <h3 className="text-2xl font-bold text-center">Please enter root database password</h3>
                        <h3 className="text-2xl font-bold text-center">{errorMessage}</h3>
                        <form onSubmit={handleSubmit}>
                            <div className="mt-4">
                                <input 
                                    type="password" 
                                    placeholder="Password" 
                                    id="password"
                                    onChange={(e) => setPassword(e.target.value)}
                                    value={password}
                                    className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                                />
                            </div>
                            <div className="flex flex-col items-center justify-between">
                                <button 
                                    className="px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-900 w-full"
                                    type="submit"
                                >
                                    Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>)
          } else {
            return( 
                <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
                    <h1>ERROR</h1>
                </div>)
          }
      }else{
        return (
          <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
              <p> {!render ? message : "Loading.."}</p>
          </div>
        )
      }
}