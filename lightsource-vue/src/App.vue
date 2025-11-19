<template>
  <RouterView />
</template>

<script setup lang="ts">
document.documentElement.dataset.theme = localStorage.getItem('ls_theme') || 'dark'
</script>

<style>
/* Global styles and CSS custom properties */
:root {
  /* Color System */
  --text: #e4e4e7;
  --muted: #71717a;
  --background: #0c0c0e;
  --panel: #18181b;
  --panel-soft: #27272a;
  --border: #3f3f46;
  --accent: #f59e0b;
  --pill: #27272a;
  --shadow: 0 4px 12px rgba(0,0,0,.4);
  --radius: 12px;
  --transition: all .2s ease;
  
  /* Spacing System (8px grid) */
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;
  --space-7: 56px;
  --space-8: 64px;
  --space-9: 72px;
  --space-10: 80px;
  
  /* Layout System */
  --container-width: 1440px;
  --content-max-width: 1440px;
  --header-height: 80px;
  
  /* Typography Scale */
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;
  --font-size-4xl: 48px;
  --font-size-5xl: 64px;
  --font-size-6xl: 72px;
  
  /* Line Heights */
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.6;
  
  /* Icon Sizes */
  --icon-sm: 16px;
  --icon-md: 24px;
  --icon-lg: 32px;
  --icon-xl: 48px;
}

:root[data-theme="light"] {
  --text: #1f2937;
  --muted: #6b7280;
  --background: #f8fafc;
  --panel: #ffffff;
  --panel-soft: #f1f5f9;
  --border: #e5e7eb;
  --accent: #2563eb;
  --pill: #f8fafc;
  --shadow: 0 4px 12px rgba(0,0,0,.1);
}

* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--background);
  color: var(--text);
  line-height: 1.6;
  font-size: 16px;
}

#app {
  min-height: 100vh;
}

/* Reset and base styles */
button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  background: none;
  color: inherit;
}

input, textarea, select {
  font-family: inherit;
  font-size: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

/* Utility classes */
.pill {
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--pill);
  color: var(--text);
  padding: 14px 28px;
  font-size: 16px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
  display: inline-block;
  font-weight: 500;
}

.pill:hover {
  border-color: #2f2f33;
  background: #25252a;
}

.pill.accent {
  background: var(--accent);
  color: #1a1a1a;
  border: none;
  font-weight: 700;
}

.pill.accent:hover {
  background: #fbbf24;
}

.pill.sm {
  padding: 8px 14px;
  font-size: 13px;
}

.pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost {
  color: var(--muted);
  font-size: 16px;
  padding: 10px 16px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost:hover {
  border-color: var(--border);
  background: rgba(255, 255, 255, 0.05);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--panel);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}

/* Responsive utilities */
@media (max-width: 767px) {
  .pill {
    padding: 12px 20px;
    font-size: 14px;
  }
  
  .ghost {
    padding: 8px 12px;
    font-size: 14px;
  }
}

@media (min-width: 1200px) {
  .pill {
    padding: 16px 32px;
    font-size: 18px;
  }
  
  .ghost {
    padding: 12px 20px;
    font-size: 16px;
  }
}
</style>
