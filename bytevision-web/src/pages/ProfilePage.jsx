import { useSnackbar } from 'notistack'
import {
  Avatar,
  Box,
  Button,
  CardContent,
  Grid,
  TextField,
  Typography,
} from '@mui/material'
import { useThemeMode } from '../contexts/ThemeContext'
import { useAppData } from '../contexts/AppDataContext'
import { PageHeader } from '../components/common/PageStates'
import { MotionCard } from '../components/common/UiKit'
import { COLORS } from '../constants/theme'
import { Stack } from '../components/common/Stack'

/**
 * Profile is local preference storage — backend has no /api/profile endpoint.
 * Activity stats shown are derived from live objectives API.
 */
export default function ProfilePage() {
  const { settings, updateSettings } = useThemeMode()
  const { objectives, overview } = useAppData()
  const { enqueueSnackbar } = useSnackbar()

  const save = () => enqueueSnackbar('Profile saved locally', { variant: 'success' })

  return (
    <Box>
      <PageHeader
        title="Profile"
        subtitle="Local profile preferences + live OKR stats from the backend"
        actions={
          <Button variant="contained" onClick={save}>
            Save profile
          </Button>
        }
      />

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 4 }}>
          <MotionCard>
            <CardContent>
              <Stack alignItems="center" spacing={2} py={2}>
                <Avatar
                  sx={{
                    width: 88,
                    height: 88,
                    bgcolor: COLORS.primary,
                    fontSize: 36,
                    fontWeight: 800,
                  }}
                >
                  {(settings.profileName || 'U').charAt(0).toUpperCase()}
                </Avatar>
                <Box textAlign="center">
                  <Typography variant="h6" fontWeight={800}>
                    {settings.profileName || 'Your Name'}
                  </Typography>
                  <Typography color="text.secondary">{settings.profileRole}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {settings.profileEmail || 'email@company.com'}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={2}>
                Edit Profile
              </Typography>
              <Stack spacing={2}>
                <TextField
                  label="Full name"
                  fullWidth
                  value={settings.profileName}
                  onChange={(e) => updateSettings({ profileName: e.target.value })}
                />
                <TextField
                  label="Email"
                  fullWidth
                  value={settings.profileEmail}
                  onChange={(e) => updateSettings({ profileEmail: e.target.value })}
                />
                <TextField
                  label="Role"
                  fullWidth
                  value={settings.profileRole}
                  onChange={(e) => updateSettings({ profileRole: e.target.value })}
                />
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <MotionCard>
            <CardContent>
              <Typography variant="h6" fontWeight={700} mb={1}>
                Linked OKR Activity (live API)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Objectives owned / visible: {objectives.length} · Overall progress:{' '}
                {overview ? `${Number(overview.overall_progress).toFixed(1)}%` : '€”'} · Active:{' '}
                {overview?.active_objectives ?? '€”'}
              </Typography>
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
