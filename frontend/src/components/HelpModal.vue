<template>
  <span class="help-wrapper">
    <button class="help-btn" @click="open = true" :title="title">?</button>

    <div v-if="open" class="modal-overlay" @click.self="open = false">
      <div class="modal help-modal">
        <div class="help-modal-header">
          <h2>{{ title }}</h2>
          <button class="close-btn" @click="open = false">✕</button>
        </div>
        <div class="help-modal-body">
          <div v-for="item in items" :key="item.title" class="help-item">
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
          </div>
        </div>
      </div>
    </div>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  title: string
  items: Array<{ title: string; text: string }>
}>()

const open = ref(false)
</script>

<style scoped>
.help-wrapper { display: inline-flex; align-items: center; }

.help-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: rgba(88, 166, 255, 0.1);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  line-height: 1;
  transition: background 0.15s, border-color 0.15s;
  flex-shrink: 0;
}
.help-btn:hover {
  background: rgba(88, 166, 255, 0.22);
  border-color: var(--accent);
}

.help-modal {
  max-width: 540px;
  width: 95vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.help-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.help-modal-header h2 { font-size: 1.1rem; }

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: color 0.15s;
}
.close-btn:hover { color: var(--text); }

.help-modal-body {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.help-item h3 {
  font-size: 0.9rem;
  color: var(--accent);
  margin-bottom: 0.25rem;
}
.help-item p {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.55;
}
</style>
