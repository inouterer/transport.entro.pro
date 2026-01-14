import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService, { User, LoginData, RegisterData, AuthResponse } from '../services/authService';
import { message } from 'antd';
import { setAuthUpdateCallback, setAuthErrorCallback } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  updateUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Проверяем авторизацию при монтировании компонента
  useEffect(() => {
    checkAuth();
    
    // Подписываемся на обновление токенов
    setAuthUpdateCallback(() => {
      // Обновляем данные пользователя после успешного refresh токена
      authService.getCurrentUser()
        .then((currentUser) => {
          setUser(currentUser);
        })
        .catch(() => {
          // Если токен невалиден, очищаем состояние
          setUser(null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
        });
    });

    // Подписываемся на ошибки авторизации (когда токен не может быть обновлен)
    setAuthErrorCallback(() => {
      // Очищаем состояние пользователя, так как токены были удалены
      setUser(null);
    });

    // Отслеживаем изменения localStorage для синхронизации состояния (между вкладками)
    const handleStorageChange = (e: StorageEvent) => {
      // Если токены были удалены в другой вкладке, обновляем состояние
      if (e.key === 'access_token' && e.newValue === null) {
        setUser(null);
      }
      // Если токены были добавлены в другой вкладке, проверяем авторизацию
      if (e.key === 'access_token' && e.newValue !== null) {
        checkAuth();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    // Очищаем callback и слушатель при размонтировании
    return () => {
      setAuthUpdateCallback(() => {});
      setAuthErrorCallback(() => {});
      window.removeEventListener('storage', handleStorageChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkAuth = async () => {
    try {
      const token = authService.getAccessToken();
      if (token) {
        // Пытаемся получить пользователя из localStorage
        const storedUser = authService.getStoredUser();
        if (storedUser) {
          setUser(storedUser);
        }

        // Проверяем валидность токена и обновляем данные пользователя
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch (error: any) {
          // Если токен невалиден (401), очищаем данные тихо
          if (error?.response?.status === 401) {
            setUser(null);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
          } else {
            console.error('Auth check error:', error);
          }
        }
      }
    } catch (error) {
      console.error('Auth check error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (data: LoginData) => {
    try {
      const response = await authService.login(data);
      setUser(response.user);
      message.success('Вход выполнен успешно!');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка входа в систему';
      message.error(errorMessage);
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await authService.register(data);
      // Устанавливаем user ТОЛЬКО если есть токены
      if (response.tokens.access_token && response.tokens.refresh_token) {
        setUser(response.user);
        message.success('Регистрация выполнена успешно!');
      } else {
        // Если токенов нет - показываем другое сообщение
        message.success('Регистрация выполнена! Проверьте почту для подтверждения.');
      }
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка регистрации';
      message.error(errorMessage);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
      message.success('Вы вышли из системы');
    } catch (error) {
      console.error('Logout error:', error);
      // Всё равно очищаем локальное состояние
      setUser(null);
    }
  };

  const updateUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Update user error:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


