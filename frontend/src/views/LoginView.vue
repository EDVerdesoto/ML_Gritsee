<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4 relative overflow-hidden">
    
    <div class="absolute left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-orange-500/20 rounded-full blur-3xl z-0 pointer-events-none"></div>

    <div class="bg-white w-full max-w-md p-8 rounded-2xl shadow-2xl relative z-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div class="flex flex-col items-center mb-8">
        <div class="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-orange-500/30 mb-3">
          G
        </div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight">Gritsee AI</h1>
        <p class="text-sm text-slate-400 font-medium">Control de Calidad Inteligente</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        
        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Usuario</label>
          <div class="relative">
            <User class="absolute left-3 top-3.5 text-slate-400 w-5 h-5" />
            <input 
              v-model="credentials.username"
              type="text" 
              placeholder="KAtest"
              required
              class="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition-all font-medium"
            >
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Contraseña</label>
          <div class="relative">
            <Lock class="absolute left-3 top-3.5 text-slate-400 w-5 h-5" />
            <input 
              v-model="credentials.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              required
              class="w-full pl-10 pr-10 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition-all font-medium"
            >
            <button 
              type="button" 
              @click="showPassword = !showPassword"
              class="absolute right-3 top-3.5 text-slate-400 hover:text-slate-600 focus:outline-none"
            >
              <Eye v-if="!showPassword" class="w-5 h-5" />
              <EyeOff v-else class="w-5 h-5" />
            </button>
          </div>
        </div>

        <div v-if="error" class="p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600 text-sm animate-pulse">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ error }}</span>
        </div>

        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full bg-slate-900 text-white font-bold py-3.5 rounded-xl hover:bg-slate-800 transition-all shadow-lg hover:shadow-xl transform active:scale-[0.98] flex items-center justify-center gap-2"
        >
          <Loader2 v-if="isLoading" class="w-5 h-5 animate-spin" />
          <span v-else>Iniciar Sesión</span>
          <ArrowRight v-if="!isLoading" class="w-4 h-4" />
        </button>

      </form>

      <div class="mt-8 text-center">
        <p class="text-xs text-slate-400">
          © {{ new Date().getFullYear() }} Gritsee Inc. Acceso restringido.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { User, Lock, Eye, EyeOff, Loader2, ArrowRight, AlertCircle } from 'lucide-vue-next';
import api from '../api/axios';
import { useUserStore } from '../stores/user';
import { useToast } from "vue-toastification";
const toast = useToast();

const router = useRouter();
const userStore = useUserStore();

// Estado
const credentials = ref({ username: '', password: '' });
const showPassword = ref(false);
const isLoading = ref(false);
const error = ref('');

const handleLogin = async () => {
  isLoading.value = true;
  error.value = '';

  try {
    // 1. Petición al Backend
    // OJO: Al usar OAuth2PasswordRequestForm, se suele enviar como Form Data
    const formData = new FormData();
    formData.append('username', credentials.value.username);
    formData.append('password', credentials.value.password);

    const response = await api.post('/api/v1/auth/token', formData);

    // 2. Manejo de Datos
    // El backend pondrá la cookie automáticamente.

    if (response.data.user) {
      userStore.setUser(response.data.user);
    }

    // 3. Redirigir
    router.push('/');

  } catch (err) {
    // Error
    if (err.response?.status === 401) {
      toast.error("Usuario o contraseña incorrectos");
    } else {
      toast.error("Error de conexión con el servidor");
    }
  } finally {
    isLoading.value = false;
  }
};
</script>