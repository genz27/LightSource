<template>
  <AppLayout>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>LightSource</h1>
        <p>AI-powered creative tools for the next generation of digital artists and developers.</p>
        <div class="hero-actions">
          <RouterLink to="/auth" class="pill accent">Get Started</RouterLink>
        </div>
      </div>
      <div class="hero-background">
        <img src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=minimalist%20abstract%20geometric%20background%20with%20soft%20gradient%20shapes%2C%20clean%20and%20modern%20design%2C%20subtle%20lighting%2C%20professional%20quality&image_size=landscape_16_9" alt="Background" />
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

    <!-- Gallery Section -->
    <section class="gallery">
      <div class="gallery-header">
        <h2>Recent Creations</h2>
        <p>Discover what our community is creating with LightSource</p>
      </div>
      <div class="gallery-grid">
        <div class="gallery-item wide">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=stunning%20landscape%20photography%20of%20mountains%20at%20sunset%20with%20vibrant%20colors%2C%20professional%20quality&image_size=landscape_16_9" alt="Mountain Landscape" />
          <div class="gallery-overlay">
            <h4>Mountain Vista</h4>
            <p>Generated in 2.1s</p>
          </div>
        </div>
        <div class="gallery-item tall">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=beautiful%20portrait%20of%20a%20person%20with%20soft%20lighting%2C%20professional%20photography%20style&image_size=portrait_4_3" alt="Portrait" />
          <div class="gallery-overlay">
            <h4>Portrait Study</h4>
            <p>Generated in 3.2s</p>
          </div>
        </div>
        <div class="gallery-item">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=futuristic%20cityscape%20with%20neon%20lights%20and%20flying%20cars%2C%20cyberpunk%20aesthetic&image_size=square" alt="Futuristic City" />
          <div class="gallery-overlay">
            <h4>Future City</h4>
            <p>Generated in 2.5s</p>
          </div>
        </div>
        <div class="gallery-item">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20abstract%20art%20with%20bold%20colors%20and%20geometric%20shapes%2C%20contemporary%20style&image_size=square" alt="Abstract Art" />
          <div class="gallery-overlay">
            <h4>Abstract Dreams</h4>
            <p>Generated in 1.8s</p>
          </div>
        </div>
        <div class="gallery-item">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=underwater%20scene%20with%20colorful%20coral%20reef%20and%20tropical%20fish%2C%20vibrant%20ocean%20life&image_size=square" alt="Underwater Scene" />
          <div class="gallery-overlay">
            <h4>Ocean Depths</h4>
            <p>Generated in 2.7s</p>
          </div>
        </div>
        <div class="gallery-item full">
          <img loading="lazy" decoding="async" fetchpriority="low" src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=space%20exploration%20scene%20with%20planets%20and%20stars%2C%20cosmic%20background%2C%20science%20fiction&image_size=landscape_16_9" alt="Space Scene" />
          <div class="gallery-overlay">
            <h4>Cosmic Journey</h4>
            <p>Generated in 2.9s</p>
          </div>
        </div>
      </div>
      <div class="gallery-actions">
        <RouterLink to="/generator" class="pill accent">Start Creating</RouterLink>
        <button class="ghost">View More</button>
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  padding: var(--space-8, 64px) 0;
  text-align: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 800px;
  margin: 0 auto;
}

.hero-content h1 {
  font-size: 72px;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 32px;
  background: linear-gradient(135deg, var(--accent) 0%, #ffffff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-content p {
  font-size: 24px;
  line-height: 1.6;
  color: var(--muted);
  margin-bottom: 48px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 24px;
  align-items: center;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  opacity: 0.3;
}

.hero-background img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(2px);
}

.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.media-showcase {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 480px;
}

.media-item {
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  animation: fadeInUp 0.6s ease-out var(--delay) both;
  position: relative;
}

.media-item.large {
  grid-column: span 2;
  grid-row: span 2;
  aspect-ratio: 16/9;
}

.media-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-overlay {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
}

.media-type {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.media-time {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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

/* Gallery Section */
.gallery {
  margin-top: 120px;
}

.gallery-header {
  text-align: center;
  margin-bottom: 64px;
}

.gallery-header h2 {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--text);
}

.gallery-header p {
  font-size: 20px;
  color: var(--muted);
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 48px;
  grid-auto-flow: dense;
}

.gallery-item {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
  cursor: pointer;
  content-visibility: auto;
  will-change: transform;
  aspect-ratio: 1 / 1;
  background: var(--panel-soft);
  box-shadow: var(--shadow);
}

.gallery-item:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: 0 10px 24px rgba(0,0,0,.35);
}

.gallery-item.wide {
  grid-column: span 2;
  aspect-ratio: 16 / 9;
}

.gallery-item.tall {
  aspect-ratio: 3 / 4;
}

.gallery-item.full {
  grid-column: 1 / -1;
  aspect-ratio: 16 / 9;
}

.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.gallery-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  color: white;
  padding: 24px;
  transform: translateY(100%);
  transition: transform 0.3s ease;
  will-change: transform;
}

.gallery-item:hover .gallery-overlay {
  transform: translateY(0);
}

.gallery-overlay h4 {
  font-size: 18px;
  margin-bottom: 4px;
}

.gallery-overlay p {
  font-size: 14px;
  opacity: 0.9;
}

.gallery-actions {
  display: flex;
  justify-content: center;
  gap: 24px;
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

/* Desktop (1200px and up) */
@media (min-width: 1200px) {
  .hero {
    padding: var(--space-8, 64px) 0;
    min-height: 50vh;
  }
  
  .hero-content h1 {
    font-size: 84px;
  }
  
  .hero-content p {
    font-size: 28px;
  }
  
  .features {
    margin-top: 160px;
  }
}

/* Tablet (768px to 1199px) */
@media (min-width: 768px) and (max-width: 1199px) {
  .hero {
    padding: var(--space-6, 48px) 0;
    min-height: 40vh;
  }
  
  .hero-content h1 {
    font-size: 64px;
  }
  
  .hero-content p {
    font-size: 22px;
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
  
  .gallery {
    margin-top: 100px;
  }
  
  .gallery-header {
    margin-bottom: 48px;
  }
  
  .gallery-header h2 {
    font-size: 40px;
  }
  
  .gallery-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-bottom: 40px;
    grid-auto-flow: dense;
  }
  
  .gallery-item.wide {
    grid-column: span 2;
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
    padding: var(--space-4, 32px) 0;
    min-height: 30vh;
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
  
  .gallery {
    margin-top: 60px;
  }
  
  .gallery-header {
    margin-bottom: 32px;
  }
  
  .gallery-header h2 {
    font-size: 32px;
  }
  
  .gallery-header p {
    font-size: 16px;
  }
  
  .gallery-grid {
    grid-template-columns: 1fr;
    grid-auto-rows: 200px;
    gap: 16px;
    margin-bottom: 32px;
  }
  
  .gallery-item.wide {
    grid-column: span 1;
  }
  
  .gallery-item.tall {
    grid-row: span 1;
  }
  
  .gallery-actions {
    flex-direction: column;
    gap: 16px;
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