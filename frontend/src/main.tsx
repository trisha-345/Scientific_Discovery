import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: '#0f172a',
          color: '#f8fafc',
          fontSize: '14px',
          borderRadius: '10px',
          padding: '12px 16px',
        },
        success: {
          iconTheme: { primary: '#22c55e', secondary: '#f8fafc' },
        },
        error: {
          iconTheme: { primary: '#ef4444', secondary: '#f8fafc' },
        },
      }}
    />
  </StrictMode>,
)