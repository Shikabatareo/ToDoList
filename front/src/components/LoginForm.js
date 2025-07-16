import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const LoginForm = () => {
    const [username,setUsername] = useState('')
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const {login} = useAuth()

    const handleSubmit = async(e)=> {
        e.preventDefault()
        setError('')
        setLoading(true)
        const result = await login(username,password)
        setLoading(false)
        if (!result.success) {
            setError(result.error)
        }
    }
    return (
        <div className="container-form">
            <form onSubmit={handleSubmit} className="form">
                <h2>Вход в систему</h2>
                <input
                    type="text"
                    placeholder="Логин"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Пароль"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Вход...' : 'Войти'}
                </button>
                {error && <p className="error">{error}</p>}
            </form>
        </div>
    );
}
export default LoginForm