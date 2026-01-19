import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // cambiar en producción
  withCredentials: true
});

// Sí mantenemos el interceptor de error por si la cookie expira
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Si el back dice "No autorizado", redirigimos al login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;