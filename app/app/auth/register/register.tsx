"use client"
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import checkAuth from "../../components/checkAuth"
import Cookie from 'js-cookie';
import Link from 'next/link';

export default function Register() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [checkPassword, setCheckPassword] = useState('')
    const [email, setEmail] = useState('')
    const [errorMessage, setError] = useState('');
    const [render, renderPage] = useState(false);
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState(100);
    const router = useRouter();  // Use this for navigation

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
            if (status === 399) {
                router.push('/auth/setup');
            } else if (status === 398) {
                router.push('/auth/rebuild');
            } else if (status >= 200 && status < 300) {
                router.push('/app/dashboard');
            }
            renderPage(true)
        }
    }, [status, loading, router]);

    const handleSubmit = async (event: { preventDefault: () => void; }) => {
        event.preventDefault(); // Prevent the default form submission

        if(password === checkPassword){

            const formData = new URLSearchParams();
            formData.append('password', password);
            formData.append('username', username);
            formData.append('email', email);



            const response = await fetch('/api/register', {
                body: formData,
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method: "POST",
            });

            if(response.ok){
                const data = await response.json();
                Cookie.set('token', data.access_token, { expires: 1 });
                router.push('/app/dashboard'); // Use router.push to navigate
            } else if(response.status === 409){
                setError("Error: Username or email already exists");

            }else{

                setError("Error: Failed to register");
            }
        }else{
            setError("Error: Passwords do not match");
        }

    };
    if(render){
        return (
            <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
                <div className="px-8 py-6 text-left bg-white shadow-lg">
                    <div>
                        <h3 className="text-2xl font-bold text-center">Register an account</h3>
                        <h3 className="text-2xl font-bold text-center">{errorMessage}</h3>
                    </div>
                    <form onSubmit={handleSubmit}>
                        <div>
                            <input 
                                type="text" 
                                placeholder="Username" 
                                id="username"
                                onChange={(e) => setUsername(e.target.value)}
                                value={username}
                                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            />
                        </div>
                        <div>
                            <input 
                                type="text" 
                                placeholder="Email" 
                                id="email"
                                onChange={(e) => setEmail(e.target.value)}
                                value={email}
                                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            />
                        </div>
                        <div>
                            <input 
                                type="password" 
                                placeholder="Password" 
                                id="password"
                                onChange={(e) => setPassword(e.target.value)}
                                value={password}
                                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            />
                        </div>
                        <div>
                            <input 
                                type="password" 
                                placeholder="Password Again" 
                                id="checkPassword"
                                onChange={(e) => setCheckPassword(e.target.value)}
                                value={checkPassword}
                                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            />
                        </div>
                        <div className="flex flex-col items-center justify-between">
                            <button 
                                className="px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-900 w-full"
                                type="submit"
                            >
                                Register
                            </button>
                            <Link href="/auth/login" className="text-sm text-blue-600 hover:underline mt-4">Login</Link>
                        </div>
                    </form>
                </div>
            </div>
        );
    }else{
        return (
            <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
                <p> {!render ? message : "Loading.."}</p>
            </div>
          )
    }
}