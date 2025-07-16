// src/components/RegisterForm.js

import React, { useState } from 'react';
import * as api from '../services/api';

const RegisterForm = ({ onRegisterSuccess }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        if (!username || !email || !password) {
            setError('Все поля обязательны для заполнения');
            setLoading(false);
            return;
        }

        try {
            const userData = { username, email, password };
            await api.register(userData);
            
            alert('Регистрация прошла успешно! Теперь вы можете войти.');
            onRegisterSuccess();

        } catch (err) {
            const errorData = await err.response?.json();
            if (errorData && errorData.detail) {
                setError(errorData.detail);
            } else {
                setError('Ошибка при регистрации. Попробуйте снова.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <form onSubmit={handleSubmit} className="form">
                <h2>Регистрация</h2>
                <input
                    type="text"
                    placeholder="Имя пользователя"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
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
                    {loading ? 'Регистрация...' : 'Зарегистрироваться'}
                </button>
                {error && <p className="error">{error}</p>}
            </form>
        </div>
    );
};

export default RegisterForm;
