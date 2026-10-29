import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult } from 'firebase/auth';

const cleanVal = (val, fallback = '') => {
  if (!val) return fallback;
  return String(val).trim().replace(/^["']|["']$/g, '');
};

const rawApiKey = cleanVal(import.meta.env.VITE_FIREBASE_API_KEY);
const isConfigured = Boolean(
  rawApiKey &&
  rawApiKey.length >= 25 &&
  !rawApiKey.includes('placeholder') &&
  !rawApiKey.includes('dummy') &&
  !rawApiKey.includes('unconfigured')
);

const firebaseConfig = {
  apiKey: isConfigured ? rawApiKey : "AIzaSyD-unconfigured-placeholder",
  authDomain: cleanVal(import.meta.env.VITE_FIREBASE_AUTH_DOMAIN, "finnk-69cc7.firebaseapp.com"),
  projectId: cleanVal(import.meta.env.VITE_FIREBASE_PROJECT_ID, "finnk-69cc7"),
  storageBucket: cleanVal(import.meta.env.VITE_FIREBASE_STORAGE_BUCKET, "finnk-69cc7.appspot.com"),
  messagingSenderId: cleanVal(import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID, "914618729958"),
  appId: cleanVal(import.meta.env.VITE_FIREBASE_APP_ID, "1:914618729958:web:fb2ce9d2c9c0dfd58dc227")
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

export async function loginWithGoogleFirebase() {
  if (!isConfigured) {
    throw new Error(
      'Configuração do Firebase pendente: Insira sua Chave de API Web do projeto "finnk-69cc7" no arquivo frontend/.env (VITE_FIREBASE_API_KEY=AIzaSy...).'
    );
  }

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    const idToken = await user.getIdToken();
    return {
      idToken,
      email: user.email,
      name: user.displayName,
      photoUrl: user.photoURL
    };
  } catch (error) {
    if (error.code === 'auth/popup-closed-by-user' || error.code === 'auth/cancelled-popup-request') {
      throw new Error('Autenticação com Google cancelada.');
    }
    if (error.code === 'auth/network-request-failed') {
      throw new Error('Falha de conexão ao autenticar com Google. Verifique sua conexão com a internet.');
    }
    if (error.code === 'auth/invalid-api-key' || error.code === 'auth/api-key-not-valid' || error.message?.includes('api-key-not-valid')) {
      throw new Error(
        'A Chave de API do Firebase informada é inválida ou expirou. Verifique a chave Web em: Console Firebase > Configurações do Projeto > Geral > Seus aplicativos.'
      );
    }
    if (error.code === 'auth/operation-not-allowed') {
      throw new Error(
        'Provedor Google desativado no Firebase. Ative-o em: Console Firebase > Authentication > Sign-in method > Google (Ativar).'
      );
    }
    throw error;
  }
}
