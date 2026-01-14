import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Result } from 'antd';
import { MailOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { Logo } from '../Logo';
import api from '../../services/api';
import { startGradientRotation, stopGradientRotation } from '../../utils/gradientAnimation';
import '../../styles/auth.css';

const { Title, Text, Paragraph } = Typography;

export const ForgotPasswordForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [email, setEmail] = useState('');

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
      await api.post('/auth/forgot-password', { email: values.email });
      setEmail(values.email);
      setSubmitted(true);
    } catch (error: any) {
      console.error('Forgot password error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="auth-background">
        <div className="auth-gradient"></div>
        <div className="auth-content">
          <Card className="auth-card">
            <Result
              status="success"
              title="Письмо отправлено!"
              subTitle={
                <div>
                  <Paragraph>
                    Мы отправили инструкции по восстановлению пароля на адрес <strong>{email}</strong>
                  </Paragraph>
                  <Paragraph type="secondary">
                    Пожалуйста, проверьте свою почту и следуйте инструкциям в письме.
                    Если письмо не пришло, проверьте папку "Спам".
                  </Paragraph>
                </div>
              }
              extra={[
                <Link to="/login" key="login">
                  <Button type="primary" icon={<ArrowLeftOutlined />}>
                    Вернуться к входу
                  </Button>
                </Link>,
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
              Восстановление пароля
            </Title>
          </div>

        <Alert
          message="Забыли пароль?"
          description="Не переживайте! Введите ваш email, и мы отправим вам ссылку для сброса пароля."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form name="forgot-password" onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Введите email' },
              { type: 'email', message: 'Введите корректный email' },
            ]}
          >
            <Input
              prefix={<MailOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="Email"
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
                marginBottom: 16,
              }}
            >
              Отправить инструкции
            </Button>

            <Link to="/login">
              <Button block icon={<ArrowLeftOutlined />}>
                Вернуться к входу
              </Button>
            </Link>
          </Form.Item>
        </Form>
        </Card>
      </div>
    </div>
  );
};

