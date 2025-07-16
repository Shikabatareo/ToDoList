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
     }
   )
   if(!response.ok) {
      if (response.status === 401) {
         localStorage.removeItem('authToken')
         window.location.reload()
      }
   }
   if (response.status===204 || response.headers.get('content-length')==='0') {
      return null
   }
   return response.json()
}

export const register =  (userData) => apiFetch('/register', {
   method: 'POST',
   body: JSON.stringify(userData)
})
export const getTasks = ()=> apiFetch('/tasks')
export const createTask = (taskData) => apiFetch('/tasks', {
   method: 'POST',
   body: JSON.stringify(taskData)
})
export const updateTask = (taskId, taskData) => apiFetch(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(taskData),
});
export const deleteTask = (taskId) => apiFetch(`/tasks/${taskId}`, {
    method: 'DELETE',
});
export const completeTask = (taskId) => apiFetch(`/tasks/${taskId}/complete`, {
    method: 'PUT',
});
export const uncompleteTask = (taskId) => apiFetch(`/tasks/${taskId}/uncomplete`, {
    method: 'PUT',
});