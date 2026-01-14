import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Divider } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, UserAddOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Logo } from '../Logo';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text } = Typography;

export const RegisterForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { isDark } = useTheme();
  const navigate = useNavigate();

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
    try {
      const response = await register({
        email: values.email,
        password: values.password,
        first_name: values.first_name,
        last_name: values.last_name,
        // Роль назначается администратором после регистрации
      });
      
      // Проверяем, получили ли мы токены
      if (response.tokens.access_token && response.tokens.refresh_token) {
        // Если токены есть - редирект на dashboard (маловероятно при регистрации)
        navigate('/dashboard');
      } else {
        // Если токенов нет - редирект на страницу ожидания подтверждения
        navigate('/registration-pending', { 
          state: { email: values.email } 
        });
      }
    } catch (error) {
      console.error('Register error:', error);
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
              Регистрация
            </Title>
          </div>

        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Введите email' },
              { type: 'email', message: 'Введите корректный email' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>

          <Form.Item name="first_name">
            <Input
              prefix={<UserOutlined />}
              placeholder="Имя"
              size="large"
            />
          </Form.Item>

          <Form.Item name="last_name">
            <Input
              prefix={<UserOutlined />}
              placeholder="Фамилия"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Введите пароль' },
              { min: 8, message: 'Минимум 8 символов' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
                message: 'Заглавная, строчная и цифра обязательны',
              },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Пароль"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Подтвердите пароль' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Пароли не совпадают'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Подтверждение пароля"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              icon={<UserAddOutlined />}
              style={{
                height: 48,
                fontSize: 16,
                fontWeight: 500,
              }}
            >
              Зарегистрироваться
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>или</Divider>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">Уже есть аккаунт? </Text>
          <Link to="/login">
            <Text strong style={{ color: '#667eea' }}>
              Войти
            </Text>
          </Link>
        </div>
        </Card>
      </div>
    </div>
  );
};

