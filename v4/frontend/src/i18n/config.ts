import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    // TODO: Add Spanish and French translations
    // es: { translation: es },
    // fr: { translation: fr },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
