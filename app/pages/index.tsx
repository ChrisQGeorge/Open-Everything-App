import { useEffect, useState } from 'react';
import { useRouter } from 'next/router'; // Import useRouter
import Cookie from 'js-cookie';

export default function Home() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState(100); // Changed from setstatus to setStatus for naming convention
    const router = useRouter(); // Initialize useRouter



    useEffect(() => {
      const token = Cookie.get('token');
      if (token) {
          fetch('/api/users/me/', {
              headers: {
                  'Authorization': `Bearer ${token}`
              }
          })
          .then(res => {
            const status = res.status;
            return res.json().then(data => ({
                status: status,
                data: data
            }))
          })
            .then(result=> {
              if (result.data && result.data.username) {
                  setLoading(false);
                  setStatus(result.status)
              }
          })
          .catch(error => {
              console.error('Error fetching data:', error);
              setLoading(false);
          });
      }
  }, [router]);


    useEffect(() => {
        // Redirect if the status is 403
        if (status === 403 || status === 401) {
            router.push('/login'); // Use router.push for redirection
        }
    }, [status, router]); // Add status and router to the dependency array
  return (
      <div>
        <p> {!loading ? message : "Loading.."}</p>
      </div>
  )
}
