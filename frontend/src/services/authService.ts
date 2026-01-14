import api from './api';

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role?: string;
}

export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface AuthResponse {
  user: User;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  };
}

class AuthService {
  /**
   * Вход в систему
   */
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', data);

    // Сохраняем токены и информацию о пользователе
    localStorage.setItem('access_token', response.data.tokens.access_token);
    localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));

    // Устанавливаем заголовок авторизации для будущих запросов
    this.setAuthorizationHeader(response.data.tokens.access_token);

    return response.data;
  }

  /**
   * Регистрация нового пользователя
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', data);

    // Проверяем, получили ли реальные токены (не пустые)
    if (response.data.tokens.access_token && response.data.tokens.refresh_token) {
      // Только если токены НЕ пустые - сохраняем
      localStorage.setItem('access_token', response.data.tokens.access_token);
      localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      this.setAuthorizationHeader(response.data.tokens.access_token);
    }
    // Если токены пустые - НЕ сохраняем, пользователь должен подтвердить email

    return response.data;
  }

  /**
   * Выход из системы
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Очищаем локальное хранилище в любом случае
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      localStorage.removeItem('activeProject');
      // Удаляем заголовок авторизации
      this.removeAuthorizationHeader();
    }
  }

  /**
   * Получение информации о текущем пользователе
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  }

  /**
   * Проверка валидности токена
   */
  async verifyToken(): Promise<boolean> {
    try {
      await api.post('/auth/verify-token');
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Обновление токена
   */
  async refreshToken(): Promise<{ access_token: string; refresh_token: string }> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    // Используем прямой вызов api без интерцепторов, чтобы избежать зацикливания
    const response = await api.post<{ access_token: string; refresh_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: new_refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', new_refresh_token);

    // Обновляем заголовок авторизации
    this.setAuthorizationHeader(access_token);

    return { access_token, refresh_token: new_refresh_token };
  }

  /**
   * Получение токена из localStorage
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Получение пользователя из localStorage
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (error) {
        return null;
      }
    }
    return null;
  }

  /**
   * Проверка аутентификации
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Установить заголовок авторизации
   */
  setAuthorizationHeader(token: string | null): void {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }

  /**
   * Удалить заголовок авторизации
   */
  removeAuthorizationHeader(): void {
    delete api.defaults.headers.common['Authorization'];
  }

  /**
   * Запрос на восстановление пароля
   */
  async forgotPassword(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email });
  }

  /**
   * Сброс пароля по токену
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }

  /**
   * Подтверждение email
   */
  async verifyEmail(token: string): Promise<{ success: boolean; message?: string; error?: string }> {
    const response = await api.get(`/auth/verify-email?token=${token}`);
    return response.data;
  }

  /**
   * Повторная отправка письма подтверждения
   */
  async resendVerification(email: string): Promise<void> {
    await api.post('/auth/resend-verification', { email });
  }
}

export default new AuthService();
