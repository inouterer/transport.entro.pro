import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, Typography, Result, Button, message } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import { Logo } from '../../components/Logo';
import authService from '../../services/authService';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text } = Typography;

export const RegistrationPendingPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [resending, setResending] = useState(false);
  const email = location.state?.email || '';

  useEffect(() => {
    const cleanup = startGradientRotation();
    return () => {
      if (cleanup) {
        stopGradientRotation(cleanup);
      }
    };
  }, []);

  const handleResendEmail = async () => {
    if (!email) {
      message.error('Email не найден');
      return;
    }

    setResending(true);
    try {
      await authService.resendVerification(email);
      message.success('Письмо отправлено повторно!');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка отправки письма';
      message.error(errorMessage);
    } finally {
      setResending(false);
    }
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

            <Result
              icon={<MailOutlined style={{ color: '#667eea', fontSize: 72 }} />}
              title="Проверьте вашу почту"
              subTitle={
                <>
                  <Text strong style={{ fontSize: 16, color: '#667eea' }}>
                    {email}
                  </Text>
                  <br />
                  <br />
                  <Text type="secondary">
                    Пожалуйста, перейдите по ссылке в письме для завершения регистрации.
                  </Text>
                </>
              }
              extra={
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Button 
                    type="primary" 
                    key="login" 
                    onClick={() => navigate('/login')}
                    size="large"
                  >
                    Перейти к входу
                  </Button>
                  <Button 
                    key="resend" 
                    onClick={handleResendEmail}
                    loading={resending}
                  >
                    Отправить письмо повторно
                  </Button>
                </div>
              }
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

