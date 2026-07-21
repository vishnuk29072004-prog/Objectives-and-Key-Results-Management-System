import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import App from './App';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2564cf' },
    secondary: { main: '#f5a623' },
    background: { default: '#f4f6fa' },
  },
  typography: {
    fontFamily: 'Segoe UI, Roboto, Arial, sans-serif',
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <App />
  </ThemeProvider>
);
