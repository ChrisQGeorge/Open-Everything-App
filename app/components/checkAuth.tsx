import Cookie from 'js-cookie';

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
            data: data
        }))
    })
    .then(result => {
        if (result.status && result.data.username) {
            return {"auth":true, "status":result.status, "message":"OK"}; // Authenticated
        }
        return {"auth":false, "status":result.status," message":"redirect to setup"};
    })
    .catch(error => {
        var errorMessage = 'Error fetching data:'+ error

        return {"auth":false, "status":500, "message":errorMessage}
    });
};

export default checkUserAuthentication;