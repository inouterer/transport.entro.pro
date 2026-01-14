// Скрипт для вращения градиента на страницах авторизации
let gradientAngle = 0;

export function startGradientRotation() {
  const gradientElement = document.querySelector('.auth-gradient') as HTMLElement;

  if (!gradientElement) {
    return null;
  }

  function rotateGradient() {
    gradientAngle = (gradientAngle + 0.3) % 360;

    // Создаем градиент с изменяющимся углом - точно как в образце
    const gradient = `linear-gradient(${gradientAngle}deg, white, rgb(20, 18, 46))`;

    if (gradientElement) {
      gradientElement.style.background = gradient;
    }
  }

  // Запускаем анимацию с частотой 60 FPS (каждые 16мс) - точно как в образце
  const intervalId = setInterval(rotateGradient, 50);

  // Возвращаем функцию для остановки анимации
  return () => clearInterval(intervalId);
}

export function stopGradientRotation(cleanup: () => void | null) {
  if (cleanup) {
    cleanup();
  }
}
