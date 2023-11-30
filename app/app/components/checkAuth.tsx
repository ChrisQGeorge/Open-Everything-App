import Cookie from 'js-cookie';

const checkUserAuthentication = async () => {
    const token = Cookie.get('token');
    const currStatus = Cookie.get('currStatus')

    return fetch('/api/users/me/', {
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
    .then(result => {
        if (result.status && result.data.username) {
            return {"auth":true, "status":result.status, "message":"OK"}; // Authenticated
        }
        Cookie.remove('token');
        Cookie.set('currStatus', result.status.toString(), { expires: 1 })
        return {"auth":false, "status":result.status," message":"redirect to setup"};
    })
    .catch(error => {
        var errorMessage = 'Error fetching data:'+ error

        return {"auth":false, "status":500, "message":errorMessage}
    });
}

export default checkUserAuthentication;