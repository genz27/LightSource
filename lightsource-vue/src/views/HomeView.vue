<template>
  <AppLayout>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-background">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
      <div class="hero-inner">
        <div class="hero-content">
          <div class="eyebrow">Create boldly with AI</div>
          <h1>LightSource</h1>
          <p>AI-powered creative tools for the next generation of digital artists and developers.</p>
          <div class="hero-actions">
            <RouterLink to="/auth" class="pill accent">Start for free</RouterLink>
            <RouterLink to="/generator" class="ghost">Launch Studio</RouterLink>
          </div>
          <div class="hero-stats">
            <div class="stat">
              <span class="stat-value">10k+</span>
              <span class="stat-label">Projects launched</span>
            </div>
            <div class="stat">
              <span class="stat-value">98%</span>
              <span class="stat-label">Customer satisfaction</span>
            </div>
            <div class="stat">
              <span class="stat-value">Instant</span>
              <span class="stat-label">Preview results</span>
            </div>
          </div>
        </div>
        <div class="hero-panel">
          <div class="panel-header">
            <span class="pill soft">Live demo</span>
            <span class="muted">Generate in seconds</span>
          </div>
          <div class="panel-body">
            <div class="panel-preview">
              <div class="preview-badge">Video</div>
              <video
                src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_video?prompt=floating%20glass%20orbs%20over%20a%20neon%20grid%20landscape%20at%20dusk%2C%20cinematic%20lighting%2C%20slow%20pan&image_size=landscape_16_9"
                autoplay
                loop
                muted
                playsinline
              ></video>
              <div class="preview-overlay">
                <p>“Cinematic dreamscape in neon.”</p>
                <span>Render time · 9s</span>
              </div>
            </div>
            <div class="panel-meta">
              <div class="meta-row">
                <span class="label">Mode</span>
                <span class="value">Text → Video</span>
              </div>
              <div class="meta-row">
                <span class="label">Model</span>
                <span class="value">Sora</span>
              </div>
              <div class="meta-row">
                <span class="label">Quality</span>
                <span class="value">4K ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Demo Video Section -->
    <section v-if="showDemo" class="demo-section">
      <div class="demo-container">
        <h2>Watch How It Works</h2>
        <div class="video-player">
          <div class="video-placeholder">
            <div class="play-button" @click="playDemo">
              <span>▶</span>
            </div>
            <p>Click to play demo video</p>
          </div>
        </div>
        <div class="demo-features">
          <div class="demo-feature">
            <svg class="demo-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6V12L16 16"/>
            </svg>
            <span>Input your prompt</span>
          </div>
          <div class="demo-feature">
            <svg class="demo-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            <span>AI generates in seconds</span>
          </div>
          <div class="demo-feature">
            <svg class="demo-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <span>Download and share</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features">
      <div class="features-header">
        <h2>Why Choose LightSource?</h2>
        <p>Powerful features that make creativity effortless</p>
      </div>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M24 4L30 18L44 24L30 30L24 44L18 30L4 24L18 18L24 4Z"/>
              <path d="M24 14V34M14 24H34"/>
            </svg>
          </div>
          <h3>Lightning Fast</h3>
          <p>Generate stunning visuals in seconds with our optimized AI models.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="24" cy="24" r="20"/>
              <path d="M24 8V24L32 32"/>
              <path d="M16 24C16 28.4183 19.5817 32 24 32C28.4183 32 32 28.4183 32 24C32 19.5817 28.4183 16 24 16C19.5817 16 16 19.5817 16 24Z"/>
            </svg>
          </div>
          <h3>Creative Control</h3>
          <p>Fine-tune every aspect of your generation with advanced parameters.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="12" y="18" width="24" height="18" rx="2"/>
              <path d="M16 18V12C16 8.68629 18.6863 6 22 6H26C29.3137 6 32 8.68629 32 12V18"/>
              <circle cx="24" cy="30" r="3"/>
              <path d="M18 36H30"/>
            </svg>
          </div>
          <h3>Private & Secure</h3>
          <p>Your creations are yours alone. Full privacy and data protection.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M24 4L36 16L24 28L12 16L24 4Z"/>
              <path d="M24 28V44"/>
              <path d="M12 16L4 24L12 32"/>
              <path d="M36 16L44 24L36 32"/>
            </svg>
          </div>
          <h3>High Quality</h3>
          <p>Professional-grade outputs suitable for commercial use.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="8" y="12" width="32" height="28" rx="4"/>
              <path d="M16 12V8C16 6.89543 16.8954 6 18 6H30C31.1046 6 32 6.89543 32 8V12"/>
              <path d="M16 36H32M20 40H28"/>
            </svg>
          </div>
          <h3>Any Device</h3>
          <p>Create anywhere with our responsive web application.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20L20 12L28 20L36 12L44 20V40C44 42.2091 42.2091 44 40 44H8C5.79086 44 4 42.2091 4 40V20L12 12L20 20L28 12L36 20"/>
              <circle cx="24" cy="24" r="4"/>
            </svg>
          </div>
          <h3>Cloud Storage</h3>
          <p>Save and organize your creations with unlimited storage.</p>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>Ready to Create?</h2>
        <p>Join thousands of creators who are already using LightSource to bring their ideas to life.</p>
        <div class="cta-actions">
          <RouterLink to="/auth" class="pill accent large">Get Started Free</RouterLink>
          <button class="ghost">Learn More</button>
        </div>
      </div>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref } from 'vue'

const showDemo = ref(false)
const isPlayingDemo = ref(false)

const playDemo = () => {
  showDemo.value = !showDemo.value
  isPlayingDemo.value = showDemo.value
}
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(167, 139, 250, 0.08));
  padding: clamp(32px, 6vw, 80px);
  margin-bottom: 48px;
}

.hero-inner {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 32px;
  align-items: center;
  z-index: 1;
}

.hero-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  filter: blur(20px);
}

.orb {
  position: absolute;
  border-radius: 50%;
  mix-blend-mode: screen;
  opacity: 0.6;
  animation: float 12s ease-in-out infinite;
}

.orb-1 {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.45), transparent 60%);
  top: -80px;
  left: -120px;
}

.orb-2 {
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(236, 72, 153, 0.38), transparent 55%);
  bottom: -40px;
  right: -120px;
  animation-delay: -4s;
}

.orb-3 {
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(52, 211, 153, 0.3), transparent 55%);
  top: 30%;
  right: 30%;
  animation-delay: -2s;
}

.hero-content {
  position: relative;
  max-width: 640px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: left;
}

.eyebrow {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: var(--accent);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 12px;
}

.hero-content h1 {
  font-size: clamp(48px, 8vw, 82px);
  font-weight: 800;
  line-height: 1.05;
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, var(--accent) 40%, #a855f7 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-content p {
  font-size: 20px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

.hero-actions {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.stat {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 14px;
  backdrop-filter: blur(10px);
}

.stat-value {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 13px;
  color: var(--muted);
}

.hero-panel {
  position: relative;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.35);
  backdrop-filter: blur(16px);
  min-height: 360px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-body {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.panel-preview {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.12), transparent 55%), rgba(255, 255, 255, 0.02);
}

.panel-preview video {
  width: 100%;
  height: 100%;
  max-height: 280px;
  object-fit: cover;
  display: block;
}

.preview-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 6px 10px;
  background: rgba(59, 130, 246, 0.22);
  color: #fff;
  border-radius: 10px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 14px;
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.6));
  color: #fff;
}

.panel-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 10px 12px;
  color: #e2e8f0;
}

.meta-row .label {
  color: rgba(226, 232, 240, 0.7);
  font-size: 13px;
}

.meta-row .value {
  font-weight: 600;
  font-size: 14px;
}

/* Demo Section */
.demo-section {
  margin-top: 120px;
  text-align: center;
}

.demo-container h2 {
  font-size: 48px;
  margin-bottom: 48px;
  color: var(--text);
}

.video-player {
  max-width: 800px;
  margin: 0 auto 48px;
}

.video-placeholder {
  background: var(--panel);
  border: 2px dashed var(--border);
  border-radius: 16px;
  padding: 80px 40px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.video-placeholder:hover {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.05);
}

.play-button {
  width: 80px;
  height: 80px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  transition: all 0.3s ease;
}

.play-button:hover {
  transform: scale(1.1);
  background: #2563eb;
}

.play-button span {
  font-size: 24px;
  color: white;
  margin-left: 4px;
}

.demo-features {
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
}

.demo-feature {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.demo-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 8px;
  opacity: 0.8;
  color: var(--accent);
}

/* Features Section */
.features {
  margin-top: 120px;
}

.features-header {
  text-align: center;
  margin-bottom: 64px;
}

.features-header h2 {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--text);
}

.features-header p {
  font-size: 20px;
  color: var(--muted);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.feature-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 48px 32px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
}

.feature-icon {
  margin-bottom: 16px;
  color: var(--accent);
  opacity: 0.8;
}

.feature-icon svg {
  width: 48px;
  height: 48px;
}

.feature-card h3 {
  font-size: 20px;
  margin-bottom: 12px;
  color: var(--text);
}

.feature-card p {
  color: var(--muted);
  line-height: 1.5;
}

/* CTA Section */
.cta-section {
  margin-top: 120px;
  text-align: center;
  padding: 80px 0;
  background: linear-gradient(135deg, var(--panel) 0%, rgba(59, 130, 246, 0.05) 100%);
  border-radius: 24px;
  border: 1px solid var(--border);
}

.cta-content h2 {
  font-size: 56px;
  margin-bottom: 24px;
  color: var(--text);
}

.cta-content p {
  font-size: 20px;
  color: var(--muted);
  margin-bottom: 48px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 24px;
  align-items: center;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0); }
}

/* Desktop (1200px and up) */
@media (min-width: 1200px) {
  .hero {
    padding: 80px;
    min-height: 55vh;
  }

  .hero-content h1 {
    font-size: 88px;
  }

  .hero-content p {
    font-size: 26px;
  }
  
  .features {
    margin-top: 160px;
  }
}

/* Tablet (768px to 1199px) */
@media (min-width: 768px) and (max-width: 1199px) {
  .hero {
    padding: 56px;
    min-height: 45vh;
  }

  .hero-content h1 {
    font-size: 64px;
  }

  .hero-content p {
    font-size: 20px;
  }
  
  .demo-section {
    margin-top: 100px;
  }
  
  .demo-container h2 {
    font-size: 40px;
    margin-bottom: 40px;
  }
  
  .demo-features {
    gap: 32px;
  }
  
  .features {
    margin-top: 100px;
  }
  
  .features-header {
    margin-bottom: 48px;
  }
  
  .features-header h2 {
    font-size: 40px;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }
  
  .cta-section {
    margin-top: 100px;
    padding: 60px 40px;
  }
  
  .cta-content h2 {
    font-size: 48px;
  }
}

/* Mobile (767px and below) */
@media (max-width: 767px) {
  .hero {
    padding: var(--space-4, 32px);
    min-height: 40vh;
  }

  .hero-inner {
    grid-template-columns: 1fr;
  }

  .hero-content {
    text-align: center;
    align-items: center;
  }

  .hero-content h1 {
    font-size: 48px;
  }
  
  .hero-content p {
    font-size: 18px;
  }
  
  .hero-actions {
    justify-content: center;
    flex-direction: column;
    gap: 16px;
  }
  
  .demo-section {
    margin-top: 60px;
  }
  
  .demo-container h2 {
    font-size: 32px;
    margin-bottom: 32px;
  }
  
  .video-placeholder {
    padding: 60px 20px;
  }
  
  .play-button {
    width: 60px;
    height: 60px;
  }
  
  .demo-features {
    gap: 24px;
  }
  
    .features {
      margin-top: 60px;
  }
  
  .features-header {
    margin-bottom: 32px;
  }
  
  .features-header h2 {
    font-size: 32px;
  }
  
  .features-header p {
    font-size: 16px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .feature-card {
    padding: 32px 24px;
  }
  
  .cta-section {
    margin-top: 60px;
    padding: 60px 20px;
  }
  
  .cta-content h2 {
    font-size: 36px;
  }
  
  .cta-content p {
    font-size: 16px;
  }
  
  .cta-actions {
    flex-direction: column;
    gap: 16px;
  }
}
</style>