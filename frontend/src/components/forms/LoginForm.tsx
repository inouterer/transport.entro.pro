import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Divider, Alert } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Logo } from '../Logo';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text } = Typography;

export const LoginForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { login } = useAuth();
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const message = location.state?.message;

  // Запуск анимации градиента при монтировании компонента
  useEffect(() => {
    const cleanup = startGradientRotation();
    return () => {
      if (cleanup) {
        stopGradientRotation(cleanup);
      }
    };
  }, []);

  const onFinish = async (values: any) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      await login({
        email: values.email,
        password: values.password,
      });
      navigate('/dashboard');
    } catch (error) {
      // Пытаемся вывести понятное сообщение из ответа сервера
      // 401: Неверный email или пароль
      // 403: Email не подтвержден
      // Остальное: общая ошибка
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err: any = error;
      const status = err?.response?.status as number | undefined;
      const detail = err?.response?.data?.detail as string | undefined;

      if (status === 401) {
        setErrorMessage('Неверный email или пароль');
      } else if (status === 403) {
        setErrorMessage(detail || 'Доступ запрещён. Возможно, email не подтверждён.');
      } else if (detail) {
        setErrorMessage(detail);
      } else {
        setErrorMessage('Не удалось выполнить вход. Попробуйте ещё раз.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-background">
      <div className="auth-gradient"></div>
      <div className="auth-content">
        <Card className="auth-card">
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'center' }}>
              <Logo size="md" variant={isDark ? "dark" : "light"} />
            </div>
            <Title level={2} style={{ marginBottom: 0 }}>
              Вход в систему
            </Title>
          </div>

          {message && (
            <Alert message={message} type="success" showIcon style={{ marginBottom: 24 }} />
          )}

          {errorMessage && (
            <Alert message={errorMessage} type="error" showIcon style={{ marginBottom: 16 }} />
          )}

          <Form name="login" onFinish={onFinish} autoComplete="off">
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Введите email' },
                { type: 'email', message: 'Введите корректный email' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Email"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Введите пароль' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Пароль"
                size="large"
              />
            </Form.Item>

            <Form.Item>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <Link to="/forgot-password">
                  <Text style={{ color: '#667eea' }}>Забыли пароль?</Text>
                </Link>
              </div>

              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                icon={<LoginOutlined />}
                style={{
                  height: 48,
                  fontSize: 16,
                  fontWeight: 500,
                }}
              >
                Войти
              </Button>
            </Form.Item>
          </Form>

          <Divider plain>или</Divider>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">Ещё нет аккаунта? </Text>
            <Link to="/register">
              <Text strong style={{ color: '#667eea' }}>
                Зарегистрироваться
              </Text>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

