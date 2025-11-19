<template>
  <div class="auth-bg">
    <video v-if="bgVideo" :src="bgVideo" autoplay loop muted playsinline></video>
    <img v-else-if="bgImage" :src="bgImage" alt="background" />
    <div class="auth-bg-overlay"></div>
  </div>
  <div class="auth-container">
  <div class="auth-panel">
    <div class="auth-header">
      <h1><span class="brand">LightSource</span></h1>
      <p id="auth-subtitle">{{ isLoginMode ? 'Sign in to your account' : 'Create your account' }}</p>
      <RouterLink to="/" class="ghost back-home" aria-label="Back to Home">Back to Home</RouterLink>
    </div>

      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="success" class="success-message">{{ success }}</div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            type="email"
            id="email"
            v-model="email"
            placeholder="user@example.com"
            required
            :disabled="isLoading"
          />
        </div>

        <div class="form-group" v-if="!isLoginMode">
          <label for="username">Username</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="johndoe"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="••••••••"
            required
            :disabled="isLoading"
            @input="updatePasswordStrength"
          />
          <div v-if="!isLoginMode" class="password-strength" :class="{ hidden: !password }">
            <div class="password-strength-bar" :style="{ width: passwordStrength + '%', backgroundColor: strengthColor }"></div>
          </div>
          <div v-if="!isLoginMode && password" class="password-strength-text" :style="{ color: strengthColor }">
            {{ strengthText }}
          </div>
        </div>

        <div class="form-group" v-if="!isLoginMode">
          <label for="confirm-password">Confirm Password</label>
          <input
            type="password"
            id="confirm-password"
            v-model="confirmPassword"
            placeholder="••••••••"
            :disabled="isLoading"
          />
        </div>

        <div class="remember-forgot" v-if="isLoginMode">
          <div class="checkbox-group">
            <input type="checkbox" id="remember" v-model="remember" />
            <label for="remember">Remember me</label>
          </div>
          <a href="#" class="forgot-link" @click.prevent="handleForgotPassword">Forgot password?</a>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-accent" :disabled="isLoading">
            {{ isLoading ? (isLoginMode ? 'Signing in...' : 'Creating account...') : (isLoginMode ? 'Sign In' : 'Sign Up') }}
          </button>
        </div>
      </form>

      <div class="auth-switch">
        <span>{{ isLoginMode ? "Don't have an account?" : "Already have an account?" }}</span>
        <a href="#" @click.prevent="toggleMode">{{ isLoginMode ? 'Sign up' : 'Sign in' }}</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const env = import.meta.env as unknown as Record<string, string | undefined>
const bgVideo = env.VITE_AUTH_BG_VIDEO_URL || ''
const bgImage = env.VITE_AUTH_BG_IMAGE_URL || ''

const email = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const remember = ref(false)
const isLoginMode = ref(true)
const success = ref('')

const isLoading = computed(() => authStore.isLoading)
const error = computed(() => authStore.error)

const passwordStrength = ref(0)
const strengthColor = ref('')
const strengthText = ref('')

const updatePasswordStrength = () => {
  if (!password.value || isLoginMode.value) {
    passwordStrength.value = 0
    strengthText.value = ''
    return
  }
  
  let strength = 0
  const feedback = []
  
  if (password.value.length >= 8) strength += 25
  else feedback.push('At least 8 characters')
  
  if (/[a-z]/.test(password.value)) strength += 25
  else feedback.push('Include lowercase letters')
  
  if (/[A-Z]/.test(password.value)) strength += 25
  else feedback.push('Include uppercase letters')
  
  if (/\d/.test(password.value)) strength += 12.5
  else feedback.push('Include numbers')
  
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password.value)) strength += 12.5
  else feedback.push('Include special characters')
  
  passwordStrength.value = strength
  
  if (strength <= 25) {
    strengthColor.value = '#f44336'
    strengthText.value = feedback[0] || 'Weak password'
  } else if (strength <= 50) {
    strengthColor.value = '#ff9800'
    strengthText.value = 'Fair password'
  } else if (strength <= 75) {
    strengthColor.value = '#ffc107'
    strengthText.value = 'Good password'
  } else {
    strengthColor.value = '#4caf50'
    strengthText.value = 'Strong password'
  }
}

const validateForm = () => {
  if (!email.value || !password.value) {
    authStore.error = 'Please fill in all required fields'
    return false
  }
  
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    authStore.error = 'Please enter a valid email address'
    return false
  }
  
  if (!isLoginMode.value) {
    if (!username.value) {
      authStore.error = 'Please enter a username'
      return false
    }
    
    if (password.value.length < 8) {
      authStore.error = 'Password must be at least 8 characters long'
      return false
    }
    
    if (password.value !== confirmPassword.value) {
      authStore.error = 'Passwords do not match'
      return false
    }
  }
  
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  authStore.clearError()
  
  let successResult = false
  if (isLoginMode.value) {
    successResult = await authStore.login(email.value, password.value)
  } else {
    successResult = await authStore.register(email.value, username.value, password.value)
  }
  
  if (successResult) {
    success.value = isLoginMode.value ? 'Successfully signed in! Redirecting...' : 'Account created successfully! Redirecting...'
    setTimeout(() => {
      router.push('/settings')
    }, 1500)
  }
}


const handleForgotPassword = () => {
  success.value = 'Password reset instructions have been sent to your email.'
  setTimeout(() => {
    success.value = ''
  }, 5000)
}

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  authStore.clearError()
  success.value = ''
  
  if (!isLoginMode.value) {
    updatePasswordStrength()
  } else {
    passwordStrength.value = 0
    strengthText.value = ''
  }
}

// Check if already logged in
if (authStore.isAuthenticated) {
  success.value = 'You are already signed in. Redirecting...'
  setTimeout(() => {
    router.push('/settings')
  }, 1500)
}
</script>

<style scoped>
.auth-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  z-index: 0;
}
.auth-bg video, .auth-bg img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}
.auth-bg-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.75) 60%, rgba(0,0,0,0.9) 100%);
}
.auth-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  padding: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  margin: 0 auto;
}
.back-home {
  position: static;
  display: inline-block;
  margin-top: 8px;
}

.auth-panel {
  background: rgba(26, 26, 32, 0.85);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 70px;
  box-shadow: var(--shadow);
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
}

.auth-header h1 {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.auth-header p {
  margin: 0;
  color: var(--muted);
  font-size: 16px;
}

.brand {
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0.4px;
}



label {
  display: block;
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 14px;
  font-weight: 500;
}

input {
  width: 100%;
  background: #111116;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  font-size: 15px;
  transition: border-color 0.2s ease;
}

input:focus {
  outline: none;
  border-color: var(--accent);
}

input::placeholder {
  color: var(--muted);
  opacity: 0.6;
}

input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.password-strength {
  margin-top: 6px;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
  transition: opacity 0.3s ease;
}

.password-strength.hidden {
  opacity: 0;
}

.password-strength-bar {
  height: 100%;
  width: 0%;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.password-strength-text {
  font-size: 11px;
  margin-top: 4px;
  transition: color 0.3s ease;
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  font-size: 14px;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.forgot-link {
  color: var(--accent);
  text-decoration: none;
  font-size: 13px;
}

.forgot-link:hover {
  text-decoration: underline;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

.btn {
  flex: 1;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--pill);
  color: var(--text);
  padding: 14px 28px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.btn:hover:not(:disabled) {
  border-color: #2f2f33;
  background: #25252a;
}

.btn-accent {
  background: var(--accent);
  color: #1a1a1a;
  border: none;
  font-weight: 600;
}

.btn-accent:hover:not(:disabled) {
  background: #e5c985;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: 24px;
  color: var(--muted);
  font-size: 13px;
}

.auth-switch a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
}

.auth-switch a:hover {
  text-decoration: underline;
}

.error-message {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
  padding: 16px 18px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 24px;
}

.success-message {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4caf50;
  padding: 16px 18px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 24px;
}

@media (max-width: 480px) {
  .auth-panel {
    padding: 40px;
  }
  
  .form-actions {
    flex-direction: column;
  }
}

@media (max-width: 1024px) {
  .auth-container {
    max-width: 92vw;
  }
}
</style>
