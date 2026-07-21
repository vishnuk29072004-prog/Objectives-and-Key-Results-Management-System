import { useSnackbar } from 'notistack'
import {
  Box,
  Button,
  CardContent,
  Divider,
  FormControlLabel,
  Grid,
  MenuItem,
  Switch,
  TextField,
  Typography,
} from '@mui/material'
import { useThemeMode } from '../contexts/ThemeContext'
import { PageHeader } from '../components/common/PageStates'
import { MotionCard } from '../components/common/UiKit'
import { Stack } from '../components/common/Stack'

/**
 * Settings are client-side preferences (theme, notifications prefs, language, profile fields).
 * There is no settings REST endpoint on the FastAPI backend.
 */
export default function SettingsPage() {
  const { mode, setMode, settings, updateSettings, toggleTheme } = useThemeMode()
  const { enqueueSnackbar } = useSnackbar()

  const save = () => {
    enqueueSnackbar('Settings saved locally', { variant: 'success' })
  }

  return (
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Theme & preferences stored in the browser (no backend settings API)"
        actions={
          <Button variant="contained" onClick={save}>
            Save
          </Button>
        }
      />

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Theme
              </Typography>
              <FormControlLabel
                control={<Switch checked={mode === 'dark'} onChange={toggleTheme} />}
                label={mode === 'dark' ? 'Dark mode' : 'Light mode'}
              />
              <Stack direction="row" spacing={1} mt={1}>
                <Button variant={mode === 'light' ? 'contained' : 'outlined'} onClick={() => setMode('light')}>
                  Light
                </Button>
                <Button variant={mode === 'dark' ? 'contained' : 'outlined'} onClick={() => setMode('dark')}>
                  Dark
                </Button>
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Notifications
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notificationsEnabled}
                    onChange={(e) => updateSettings({ notificationsEnabled: e.target.checked })}
                  />
                }
                label="Enable in-app notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailDigests}
                    onChange={(e) => updateSettings({ emailDigests: e.target.checked })}
                  />
                }
                label="Email digests (preference only €” SMTP is server-side)"
              />
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Language
              </Typography>
              <TextField
                select
                fullWidth
                label="Language"
                value={settings.language}
                onChange={(e) => updateSettings({ language: e.target.value })}
              >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="hi">Hindi</MenuItem>
                <MenuItem value="es">Spanish</MenuItem>
              </TextField>
              <FormControlLabel
                sx={{ mt: 2 }}
                control={
                  <Switch
                    checked={settings.compactMode}
                    onChange={(e) => updateSettings({ compactMode: e.target.checked })}
                  />
                }
                label="Compact mode"
              />
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Security
              </Typography>
              <Typography variant="body2" color="text.secondary">
                The FastAPI backend currently exposes open REST endpoints with no JWT/OAuth. Security settings
                (password, 2FA) are unavailable until the API adds auth.
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Typography variant="caption" color="text.secondary">
                API base: http://localhost:8000
              </Typography>
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
