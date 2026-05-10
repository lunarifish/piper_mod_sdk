import {
  createToaster,
  Toaster,
  ToastRoot,
  ToastTitle,
  ToastDescription,
  ToastCloseTrigger,
} from '@chakra-ui/react'

export const toaster = createToaster({
  placement: 'bottom-end',
  duration: 3000,
  max: 5,
})

export function AppToaster() {
  return (
    <Toaster toaster={toaster}>
      {(toast) => (
        <ToastRoot key={toast.id} minW="300px" data-type={toast.type}>
          {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
          {toast.description && <ToastDescription>{toast.description}</ToastDescription>}
          <ToastCloseTrigger />
        </ToastRoot>
      )}
    </Toaster>
  )
}
