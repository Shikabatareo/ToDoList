import React, { createContext, useState, useContext } from 'react';
const AuthContext = createContext(null)
export const AuthProvider = ({children})=> {
    const [token,setToken] = useState(localStorage.getItem('authToken'))
    const login = async(username,password)=> {
        try {
            const formData = new URLSearchParams()
            formData.append('username',username)
            formData.append('password',password)

            const response = await fetch('http://localhost:8000/token', {
                method: 'POST',
                headers: {'Content-type': 'application/x-www-form-urlencoded'},
                body: formData
            })
            if(!response.ok) {
                throw new Error('Неверный логин или пароль')
            }
            const data = await response.json()
            localStorage.setItem('authToken',data.access_token)
            setToken(data.access_token)
            return({success: true})
        }
        catch (error) {
            console.error("Ошибка входа:", error);
            return { success: false, error: error.message };
    }
    
}
const logout =()=> {
    localStorage.removeItem('authToken')
    setToken(null)
}

const value = {token,login,logout}
return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export const useAuth=()=> {
return useContext(AuthContext)
}