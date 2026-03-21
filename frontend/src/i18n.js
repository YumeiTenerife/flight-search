import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslations from './locales/en.json';
import esTranslations from './locales/es.json';

const resources = {
  en: { translation: enTranslations },
  es: { translation: esTranslations }
};

// Detect user language from browser settings
const detectLanguage = () => {
  const stored = window.localStorage.getItem('language');
  if (stored && ['en', 'es'].includes(stored)) return stored;
  
  const browserLang = (navigator.language || navigator.userLanguage || 'en').split('-')[0];
  return ['en', 'es'].includes(browserLang) ? browserLang : 'en';
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: detectLanguage(),
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
