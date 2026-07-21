import { memo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Skeleton,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import { motion } from 'framer-motion'
import { Stack } from './Stack'

function StatCard({ title, value, subtitle, icon, color, loading, trend }) {
  const theme = useTheme()
  const accent = color || theme.palette.primary.main

  if (loading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Skeleton width="40%" height={20} />
          <Skeleton width="60%" height={40} sx={{ mt: 1 }} />
          <Skeleton width="50%" height={16} sx={{ mt: 1 }} />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card
      component={motion.div}
      whileHover={{ y: -4, transition: { type: 'spring', stiffness: 300, damping: 20 } }}
      sx={{
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'default',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: -20,
          right: -20,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(accent, 0.18)} 0%, transparent 70%)`,
        }}
      />
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={500}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={800} sx={{ mt: 0.5, color: accent }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
                {trend}
              </Typography>
            )}
          </Box>
          {icon && (
            <Box
              sx={{
                p: 1.25,
                borderRadius: 2.5,
                bgcolor: alpha(accent, 0.12),
                color: accent,
                display: 'flex',
              }}
            >
              {icon}
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}

export default memo(StatCard)
