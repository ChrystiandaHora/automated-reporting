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
  border-radius: 2px;
  border: 2px solid var(--border);
  background: transparent;
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 800;
  cursor: pointer;
  line-height: 1;
  box-shadow: 2px 2px 0 var(--accent);
  transition: transform 0.1s, box-shadow 0.1s, background 0.1s;
  flex-shrink: 0;
}
.help-btn:hover {
  background: var(--accent);
  color: var(--bg);
  transform: translateY(-1px) translateX(-1px);
  box-shadow: 3px 3px 0 var(--accent);
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
  border-bottom: 2px solid var(--accent);
  padding-bottom: 0.75rem;
}
.help-modal-header h2 { font-size: 1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }

.close-btn {
  background: transparent;
  border: 2px solid var(--border);
  color: var(--text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.15rem 0.4rem;
  border-radius: 0;
  transition: background 0.1s, color 0.1s;
}
.close-btn:hover { background: #f85149; color: #fff; border-color: #f85149; }

.help-modal-body {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.help-item h3 {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.3rem;
}
.help-item p {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.55;
}
</style>
