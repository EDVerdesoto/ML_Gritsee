import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/axios';

export const useUserStore = defineStore('user', () => {
  const user = ref(null);

  // Intentar recuperar usuario de localStorage (solo datos públicos de UI)
  const storedUser = localStorage.getItem('user_public_data');
  if (storedUser) {
    user.value = JSON.parse(storedUser);
  }

  const setUser = (userData) => {
    user.value = userData;
    // Persistir solo datos públicos de UI (username, is_active)
    // El token JWT NUNCA toca localStorage, está en cookie HttpOnly
    localStorage.setItem('user_public_data', JSON.stringify(userData));
  };

  const clearUser = () => {
    user.value = null;
    localStorage.removeItem('user_public_data');
  };

  const logout = async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    } finally {
      clearUser();
    }
  };

  // Verifica la sesión con el backend (lee la cookie automáticamente)
  const checkAuth = async () => {
    try {
      const response = await api.get('/api/v1/auth/me');
      user.value = response.data;
      return true;
    } catch (error) {
      user.value = null;
      return false;
    }
  };

  return { user, setUser, clearUser, logout, checkAuth };
});