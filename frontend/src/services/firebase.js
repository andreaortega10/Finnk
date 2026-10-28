import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyD-finnk-dummy-key-placeholder",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "finnk-69cc7.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "finnk-69cc7",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "finnk-69cc7.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "100000000000",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:100000000000:web:0000000000000000000000"
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

export async function loginWithGoogleFirebase() {
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
      throw new Error('Falha de conexão ao autenticar com Google. Verifique sua internet.');
    }
    if (error.code === 'auth/invalid-api-key' || error.code === 'auth/api-key-not-valid') {
      throw new Error('Chave de API do Firebase não configurada. Configure VITE_FIREBASE_API_KEY no painel do Firebase.');
    }
    throw error;
  }
}
