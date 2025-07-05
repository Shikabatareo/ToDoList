const API_URL = 'http://localhost:8000';

const apiFetch = async(endpoint,options={})=> {
     const token = localStorage.getItem('authToken');
     const headers = {
        'Content-Type': 'application/json',
        ...options.headers
     }
     if(token) {
        headers['Authorization'] = `Bearer ${token}`
     }
     const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
     })
}