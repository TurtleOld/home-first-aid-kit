<script setup>
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
</script>

<template>
  <main class="app-shell">
    <section class="hero">
      <p class="eyebrow">MVP</p>
      <h1>Домашняя аптечка</h1>
      <p class="lede">
        Каркас Vue/Vite/PWA готов. Следующая фаза добавит регистрацию семьи,
        приглашения и защищённый API.
      </p>
      <a :href="`${apiBaseUrl}/health/`" target="_blank" rel="noreferrer">Проверить API</a>
    </section>
  </main>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  color: #172033;
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.14), transparent 38%),
    linear-gradient(315deg, rgba(245, 158, 11, 0.16), transparent 42%),
    #f8fafc;
}

.hero {
  width: min(720px, 100%);
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
  color: #0f766e;
}

h1 {
  margin: 0;
  font-size: clamp(2.5rem, 9vw, 5rem);
  line-height: 0.95;
}

.lede {
  max-width: 560px;
  margin: 24px 0;
  font-size: 1.1rem;
  line-height: 1.6;
  color: #475569;
}

a {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  padding: 0 18px;
  border-radius: 8px;
  color: #ffffff;
  background: #0f766e;
  font-weight: 700;
  text-decoration: none;
}

@media (prefers-color-scheme: dark) {
  .app-shell {
    color: #f8fafc;
    background:
      linear-gradient(135deg, rgba(45, 212, 191, 0.16), transparent 38%),
      linear-gradient(315deg, rgba(251, 191, 36, 0.12), transparent 42%),
      #111827;
  }

  .lede {
    color: #cbd5e1;
  }
}
</style>

