import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Result } from 'antd';
import { LockOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Logo } from '../Logo';
import api from '../../services/api';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text, Paragraph } = Typography;

export const ResetPasswordForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

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
    if (!token) {
      setError('Токен восстановления пароля не найден');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: values.password,
      });
      setSuccess(true);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || 'Ошибка при сбросе пароля. Попробуйте снова.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="auth-background">
        <div className="auth-gradient"></div>
        <div className="auth-content">
          <Card className="auth-card">
            <Result
              status="error"
              title="Недействительная ссылка"
              subTitle="Токен восстановления пароля не найден или устарел"
              extra={[
                <Link to="/forgot-password" key="forgot">
                  <Button type="primary">Запросить новую ссылку</Button>
                </Link>,
                <Link to="/login" key="login">
                  <Button>Вернуться к входу</Button>
                </Link>,
              ]}
            />
          </Card>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="auth-background">
        <div className="auth-gradient"></div>
        <div className="auth-content">
          <Card className="auth-card">
            <Result
              status="success"
              icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              title="Пароль успешно изменен!"
              subTitle="Теперь вы можете войти в систему с новым паролем"
              extra={[
                <Button
                  type="primary"
                  key="login"
                  onClick={() => navigate('/login', { state: { message: 'Пароль успешно изменен!' } })}
                >
                  Войти в систему
                </Button>,
              ]}
            />
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-background">
      <div className="auth-gradient"></div>
      <div className="auth-content">
        <Card className="auth-card">
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'center' }}>
              <Logo size="lg" />
            </div>
            <Title level={2} style={{ marginBottom: 0 }}>
              Создание нового пароля
            </Title>
          </div>

          {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}

        <Form name="reset-password" onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Введите новый пароль' },
              { min: 8, message: 'Пароль должен содержать минимум 8 символов' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
                message: 'Пароль должен содержать заглавную букву, строчную букву и цифру',
              },
            ]}
            hasFeedback
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="Новый пароль"
            />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: 'Подтвердите новый пароль' },
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
              prefix={<LockOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="Подтвердите новый пароль"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 48,
                fontSize: 16,
                fontWeight: 500,
              }}
            >
              Сбросить пароль
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Link to="/login">
            <Text style={{ color: '#667eea' }}>Вернуться к входу</Text>
          </Link>
        </div>
        </Card>
      </div>
    </div>
  );
};

