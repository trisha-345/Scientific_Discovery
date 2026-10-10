import toast from 'react-hot-toast'

export const notify = {
  success: (msg: string) => toast.success(msg, { duration: 3000 }),
  error: (msg: string) => toast.error(msg, { duration: 5000 }),
  loading: (msg: string) => toast.loading(msg),
  dismiss: (id?: string) => toast.dismiss(id),
  promise: <T,>(
    p: Promise<T>,
    msgs: { loading: string; success: string; error: string }
  ) => toast.promise(p, msgs),
}