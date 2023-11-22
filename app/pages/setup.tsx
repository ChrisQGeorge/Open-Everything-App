import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function Login() {
    const [password, setPassword] = useState('');
    const [status, setStatus] = useState(100)
    const router = useRouter();

    useEffect(() => {
        fetch('/api/users/me/')
          .then(res => {
            const status = res.status;
            return res.json().then(data => ({
                status: status,
                data: data
            }));
        }).then(result => {
            setStatus(result.status); // Update the status state
        }).catch(error => {
            console.error('Error fetching data:', error);
        });
    }, []);

    if(status/ 100 == 2){
        router.push('/dashboard')
    }else if(status == 307){
        router.push
    }


    const handleSubmit = async (event: { preventDefault: () => void; }) => {
        event.preventDefault();
        // Implement your login logic here
        console.log('Saved Pass:', password);
        // On successful login, redirect or handle the response
        // router.push('/dashboard'); // Redirect to dashboard or relevant page
    };

    return (
        <div className="text-black flex items-center justify-center min-h-screen bg-gray-200">
            <div className="px-8 py-6 text-left bg-white shadow-lg">
                <h3 className="text-2xl font-bold text-center">Please select a root database password</h3>
                <h3 className="text-lg font-bold text-center">Save this password!!! You won`&apos;`t be able to persist changes over rebuilds otherwise!</h3>
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
        </div>
    );
}