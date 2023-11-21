import { useEffect, useState } from 'react';
import Cookie from 'js-cookie';

export default function Home() {
        const [message, setMessage] = useState("");
        const [loading, setLoading] = useState(true);
    
        useEffect(() => {
          const token = Cookie.get('token');
          if (token) {
              fetch('/api/users/me/', {
                  headers: {
                      'Authorization': `Bearer ${token}`
                  }
              })
              .then(res => res.json())
              .then(data => {
                  setMessage("Your username is "+data.username)
                  setLoading(false)
              })
              .catch(error => {
                  setMessage('Error fetching data:'+error);
              });
          }
      }, []);

      return (
        <div>
          <p> {!loading ? message : "Loading.."}</p>
        </div>
      )
    }