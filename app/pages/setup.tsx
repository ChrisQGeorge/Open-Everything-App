import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function Setup() {
    const [loading, setLoading] = useState(true);
    const [content, setContent] = useState(``);
    const [password, setPassword] = useState("")
    const [firstTimeStartup, setFirstTimeStartup] = useState(false);
    const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
    const router = useRouter(); // Initialize useRouter
    const [errorMessage, setError] = useState('');



    useEffect(() => {
        fetch('/setup/firstTimeStartup')
        .then(res => {
        const status = res.status;
        return res.json().then(data => ({
            status: status,
            data: data
        }))
        })
        .then(result=> {
            if (result.data === false) {
                setLoading(false);
                setStatus(result.status)
                throw new Error('Internal Server Error');
            }else{
                setFirstTimeStartup(true)
            }
        })
        .catch(error => {
            setLoading(false);
            setStatus(400)
            throw new Error('Internal Server Error');
        });
  }, []);

  const handleSubmit = async (event: { preventDefault: () => void; }) => {
        event.preventDefault(); // Prevent the default form submission

        const response = await fetch('/api/setup/setRoot', {
            body: `password=${encodeURIComponent(password)}`,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method: "POST",
        });

        if(response.ok){
            const data = await response.json();
            router.push('/login'); // Use router.push to navigate
        } else {
            setError("Error: Failed to set root password");
        }
    };


  

  if (firstTimeStartup === true){
    return(
        <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
            <div className="px-8 py-6 text-left bg-white shadow-lg">
                <h3 className="text-2xl font-bold text-center">Please select a root database password</h3>
                <h3 className="text-lg font-bold text-center">Save this password!!! You won\`&apos;\`t be able to persist changes over rebuilds otherwise!</h3>
                <h3 className="text-2xl font-bold text-center">{errorMessage}</h3>
                <form onSubmit={handleSubmit}>
                    <div className="mt-4">
                        <label className="block" htmlFor="password">Password</label>
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
                        <a href="#" className="text-sm text-blue-600 hover:underline mt-4">Forgot password?</a>
                    </div>
                </form>
            </div>
        </div>)
  } else {
    return( 
        <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
            <h1>ERROR: App already set up</h1>
        </div>)
  }
}