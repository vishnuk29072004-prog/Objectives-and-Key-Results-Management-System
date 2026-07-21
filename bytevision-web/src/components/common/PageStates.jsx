import { memo } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Typography,
} from '@mui/material'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined'
import RefreshIcon from '@mui/icons-material/Refresh'
import InboxIcon from '@mui/icons-material/Inbox'
import { motion } from 'framer-motion'
import { Stack } from './Stack'

export const LoadingBlock = memo(function LoadingBlock({ rows = 3 }) {
  return (
    <Stack spacing={2}>
      {Array.from({ length: rows }).map((_, i) => (
        <Card key={i}>
          <CardContent>
            <Box sx={{ height: 16, bgcolor: 'action.hover', borderRadius: 1, width: '40%', mb: 1 }} />
            <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1, width: '80%', mb: 0.5 }} />
            <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1, width: '60%' }} />
          </CardContent>
        </Card>
      ))}
    </Stack>
  )
})

export const EmptyState = memo(function EmptyState({
  title = 'Nothing here yet',
  description = 'Data from the backend will appear here once available.',
  action,
}) {
  return (
    <Box
      component={motion.div}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      sx={{
        py: 8,
        px: 3,
        textAlign: 'center',
        borderRadius: 3,
        border: '1px dashed',
        borderColor: 'divider',
      }}
    >
      <InboxIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
      <Typography variant="h6" fontWeight={700}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 2, maxWidth: 420, mx: 'auto' }}>
        {description}
      </Typography>
      {action}
    </Box>
  )
})

export const ErrorState = memo(function ErrorState({ message, onRetry }) {
  return (
    <Alert
      severity="error"
      icon={<ErrorOutlineIcon />}
      action={
        onRetry ? (
          <Button color="inherit" size="small" startIcon={<RefreshIcon />} onClick={onRetry}>
            Retry
          </Button>
        ) : null
      }
      sx={{ borderRadius: 2 }}
    >
      <Typography fontWeight={600}>Something went wrong</Typography>
      <Typography variant="body2">{message || 'Unable to reach the API.'}</Typography>
    </Alert>
  )
})

export const PageHeader = memo(function PageHeader({ title, subtitle, actions }) {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      justifyContent="space-between"
      alignItems={{ xs: 'stretch', sm: 'center' }}
      spacing={2}
      mb={3}
    >
      <Box>
        <Typography variant="h4" fontWeight={800}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {actions && (
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {actions}
        </Stack>
      )}
    </Stack>
  )
})
