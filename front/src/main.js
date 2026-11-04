import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './style.css'
import 'driver.js/dist/driver.css'
import './onboarding/onboarding.css'
import App from './App.vue'
import router from './route/router'

function reportUiError(error) {
  console.error(error)
  window.dispatchEvent(new CustomEvent('ruinion-app-error', { detail: error }))
}

const app = createApp(App)
const pinia = createPinia()


app.config.errorHandler = reportUiError
router.onError(reportUiError)

app.use(pinia).use(router).mount('#app')
