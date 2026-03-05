import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-react'
import { useEffect, useState } from 'react'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

interface ToastProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastProps) {
  useEffect(() => {
    const duration = toast.duration || 5000
    const timer = setTimeout(() => onRemove(toast.id), duration)
    return () => clearTimeout(timer)
  }, [toast.id, toast.duration, onRemove])

  const icons = {
    success: CheckCircle,
    error: AlertTriangle,
    warning: AlertTriangle,
    info: Info,
  }

  const styles = {
    success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
    error: 'border-red-500/30 bg-red-500/10 text-red-300',
    warning: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
    info: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  }

  const Icon = icons[toast.type]

  return (
    <motion.div
      initial={{ opacity: 0, x: 300, scale: 0.8 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.8 }}
      transition={{ duration: 0.3, type: 'spring', stiffness: 200 }}
      className={`glass-card p-4 flex items-center space-x-3 min-w-[320px] border ${styles[toast.type]}`}
    >
      <Icon className="w-5 h-5 shrink-0" />
      <span className="flex-1 text-sm font-medium">{toast.message}</span>

      <motion.button
        onClick={() => onRemove(toast.id)}
        className="text-gray-400 hover:text-white transition-colors"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <X className="w-4 h-4" />
      </motion.button>
    </motion.div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onRemove={onRemove}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

// Custom Hook for managing toasts
export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = crypto.randomUUID() // safer unique ID
    setToasts((prev) => [...prev, { ...toast, id }])
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  return {
    toasts,
    addToast,
    removeToast,
  }
}

// ── Global Toast Context ─────────────────────────────────
import { createContext, useContext, useCallback } from 'react'

interface ToastContextValue {
  addToast: (toast: Omit<Toast, 'id'>) => void
  success: (message: string) => void
  error: (message: string) => void
  warning: (message: string) => void
  info: (message: string) => void
}

const ToastContext = createContext<ToastContextValue>({
  addToast: () => {},
  success: () => {},
  error: () => {},
  warning: () => {},
  info: () => {},
})

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { toasts, addToast, removeToast } = useToast()

  const success = useCallback((message: string) => addToast({ type: 'success', message }), [addToast])
  const error = useCallback((message: string) => addToast({ type: 'error', message }), [addToast])
  const warning = useCallback((message: string) => addToast({ type: 'warning', message }), [addToast])
  const info = useCallback((message: string) => addToast({ type: 'info', message }), [addToast])

  return (
    <ToastContext.Provider value={{ addToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useGlobalToast() {
  return useContext(ToastContext)
}