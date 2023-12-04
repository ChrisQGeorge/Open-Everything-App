import Cookie from 'js-cookie';

const blankUser = {
    'username':"",
    'email':"",
    'profile_image':"",
    'attributes':[""],
    'roles':[""],
    'settings':[""]
}

const checkUserAuthentication = async () => {
    const token = Cookie.get('token');

    return fetch('/api/users/me/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(res => {
        const status = res.status;
        return res.json().then(data => ({
            status: status,
            user: data
        }))
    })
    .then(result => {
        if (result.status && result.user.username) {
            return {"auth":true, "status":result.status, "message":"OK", 'data':result.user}; // Authenticated
        }
        Cookie.remove('token');
        Cookie.set('currStatus', result.status.toString(), { expires: 1 })
        return {"auth":false, "status":result.status," message":"redirect to setup", data:blankUser};
    })
    .catch(error => {
        var errorMessage = 'Error fetching data:'+ error

        return {"auth":false, "status":500, "message":errorMessage, data:blankUser}
    });
}

export default checkUserAuthentication;