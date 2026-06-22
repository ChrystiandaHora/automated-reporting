<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div 
        v-for="toast in toastStore.toasts" 
        :key="toast.id" 
        class="toast-card" 
        :class="`toast-${toast.type}`"
        @click="toastStore.removeToast(toast.id)"
      >
        <span class="toast-message">{{ toast.message }}</span>
        <button class="toast-close">&times;</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from '../stores/toast'

const toastStore = useToastStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 400px;
  width: 90vw;
}

.toast-card {
  background: var(--card-bg);
  color: var(--text);
  border: 2px solid var(--border);
  padding: 1rem 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;
}

.toast-info {
  border-color: var(--accent);
  box-shadow: 4px 4px 0 var(--accent);
}

.toast-success {
  border-color: #3fb950;
  box-shadow: 4px 4px 0 #3fb950;
}

.toast-error {
  border-color: #f85149;
  box-shadow: 4px 4px 0 #f85149;
}

.toast-message {
  line-height: 1.4;
  flex: 1;
}

.toast-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
  transition: color 0.1s;
}
.toast-close:hover {
  color: var(--text);
}

/* Transições da Animação do Vue */
.toast-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}
</style>
