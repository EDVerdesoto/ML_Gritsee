<template>
  <div class="flex flex-col h-full bg-white border-r border-slate-200"> <div class="p-6 flex items-center gap-3">
      <div class="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center text-white font-bold shadow-lg shadow-orange-500/20">G</div>
      <span class="text-xl font-bold tracking-tight text-slate-900">Gritsee AI</span>
    </div>
    
    <nav class="flex-1 px-4 space-y-2 mt-4">
      
      <router-link to="/" 
        class="flex items-center gap-3 px-4 py-3 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
        exact-active-class="!bg-amber-500/10 !text-orange-600 font-medium">
        <LayoutDashboard class="w-5 h-5" />
        <span>Dashboard</span>
      </router-link>
      
      <router-link to="/carga" 
        class="flex items-center gap-3 px-4 py-3 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
        active-class="!bg-amber-500/10 !text-orange-600 font-medium">
        <UploadCloud class="w-5 h-5" />
        <span>Cargar Inspección</span>
      </router-link>

      <router-link to="/historial" 
        class="flex items-center gap-3 px-4 py-3 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
        active-class="!bg-amber-500/10 !text-orange-600 font-medium">
        <History class="w-5 h-5" />
        <span>Historial</span>
      </router-link>
    </nav>

    <div class="p-4 border-t border-slate-200">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600">AD</div>
        <div>
          <p class="text-sm font-medium text-slate-900">Admin</p>
          <p class="text-xs text-slate-500">Gerente de Calidad</p>
        </div>
      </div>
      
      <button 
        @click="handleLogout"
        class="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium">
        <LogOut class="w-4 h-4" />
        <span>Cerrar Sesión</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { LayoutDashboard, History, UploadCloud, LogOut } from 'lucide-vue-next';
import { useUserStore } from '../../stores/user';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const router = useRouter();

const handleLogout = async () => {
  await userStore.logout();
  router.push('/login');
};
</script>