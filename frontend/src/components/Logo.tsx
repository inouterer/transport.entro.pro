import React from 'react';
import logoBlue from '../assets/images/entro-gtm-logo_blue.svg';
import logoWhite from '../assets/images/entro-gtm-logo_white.svg';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'light' | 'dark' | 'auto';
}

export const Logo: React.FC<LogoProps> = ({ size = 'md', variant = 'auto' }) => {
  const sizeMap = {
    sm: 80,
    md: 120,
    lg: 160,
    xl: 213,
  };

  const currentSize = sizeMap[size];
  
  // Выбор логотипа в зависимости от варианта
  // dark theme → light (white) logo
  // light theme → dark (blue) logo
  const logoSource = variant === 'dark' ? logoWhite : logoBlue;
  
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center' }}>
      <img 
        src={logoSource} 
        alt="ЭНТРО.ГТМ" 
        style={{ 
          height: currentSize,
          width: 'auto',
        }}
      />
    </div>
  );
};

