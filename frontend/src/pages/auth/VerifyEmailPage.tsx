import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Result, Button, Spin } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { Logo } from '../../components/Logo';
import api from '../../services/api';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text } = Typography;

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  // Запуск анимации градиента при монтировании компонента
  useEffect(() => {
    const cleanup = startGradientRotation();
    return () => {
      if (cleanup) {
        stopGradientRotation(cleanup);
      }
    };
  }, []);

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('Токен подтверждения не найден');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await api.get(`/auth/verify-email?token=${token}`);

      if (response.data.success) {
        setStatus('success');
        setMessage(response.data.message || 'Email успешно подтвержден!');
      } else {
        setStatus('error');
        setMessage(response.data.error || 'Ошибка подтверждения email');
      }
    } catch (error: any) {
      setStatus('error');
      setMessage(
        error.response?.data?.detail || 'Произошла ошибка при подтверждении email'
      );
    }
  };

  const handleGoToLogin = () => {
    navigate('/login', {
      state: { message: 'Email подтвержден! Теперь вы можете войти в систему.' },
    });
  };

  return (
    <div className="auth-background">
      <div className="auth-gradient"></div>
      <div className="auth-content">
        <div style={{ maxWidth: 600, width: '100%' }}>
          <Card className="auth-card">
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <Logo size="lg" />
              </div>
            </div>

            {status === 'loading' && (
            <Result
              icon={<Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />}
              title="Подтверждение email"
              subTitle="Проверяем ваш токен подтверждения..."
            />
          )}

          {status === 'success' && (
            <Result
              status="success"
              icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              title="Email подтвержден!"
              extra={[
                <Button type="primary" key="login" onClick={handleGoToLogin} size="large">
                  Перейти к входу
                </Button>,
              ]}
            />
          )}

          {status === 'error' && (
            <Result
              status="error"
              icon={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              title="Ошибка подтверждения"
              subTitle={message}
              extra={[
                <Button type="primary" key="login" onClick={() => navigate('/login')} size="large">
                  Вернуться к входу
                </Button>,
                <Button key="register" onClick={() => navigate('/register')}>
                  Регистрация
                </Button>,
              ]}
            />
          )}
          </Card>
        </div>
      </div>
    </div>
  );
};
