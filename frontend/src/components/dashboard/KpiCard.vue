<template>
  <div :class="[
    'glass-card rounded-2xl p-6 shadow-sm',
    highlight ? 'border-l-4 border-l-amber-500 border-t-0 border-r-0 border-b-0' : ''
  ]">
    <div class="flex justify-between items-start mb-2">
      <span class="text-slate-500 text-xs uppercase font-semibold">{{ title }}</span>
      <div :class="['p-2 rounded-lg', iconBg, iconColor]">
        <component :is="icon" class="w-4 h-4" />
      </div>
    </div>

    <div class="flex items-baseline gap-2">
      <h3 class="text-3xl font-bold text-slate-800">{{ value }}</h3>
      
      <span v-if="trendValue !== null && trendValue !== undefined" 
           :class="['text-xs font-medium flex items-center', trendColorClass]">
        <component :is="trendIcon" class="w-3 h-3 mr-0.5" />
        {{ Math.abs(trendValue) }}{{ trendUnit }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { ArrowUp, ArrowDown } from 'lucide-vue-next';

const props = defineProps({
  title: String,
  value: [String, Number],
  icon: [Object, Function],
  iconColor: { type: String, default: 'text-blue-600' },
  iconBg: { type: String, default: 'bg-blue-100' },
  trendValue: Number,
  trendUnit: { type: String, default: '%' },
  isInverse: { type: Boolean, default: false },
  highlight: { type: Boolean, default: false }
});

const trendIcon = computed(() => {
  if (!props.trendValue) return null;
  return props.trendValue >= 0 ? ArrowUp : ArrowDown;
});

const trendColorClass = computed(() => {
  if (!props.trendValue) return 'text-slate-400';
  const isPositive = props.trendValue >= 0;
  const isGood = props.isInverse ? !isPositive : isPositive;
  return isGood ? 'text-emerald-500' : 'text-red-500';
});
</script>