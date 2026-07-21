import { BrowserRouter } from 'react-router-dom'
import { SnackbarProvider } from 'notistack'
import { ThemeProvider } from './contexts/ThemeContext'
import { AppDataProvider } from './contexts/AppDataContext'
import AppRouter from './routes/AppRouter'

export default function App() {
  return (
    <ThemeProvider>
      <SnackbarProvider
        maxSnack={4}
        autoHideDuration={4000}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <AppDataProvider>
          <BrowserRouter>
            <AppRouter />
          </BrowserRouter>
        </AppDataProvider>
      </SnackbarProvider>
    </ThemeProvider>
  )
}
