import { memo, useState } from 'react'
import {
  Box,
  Button,
  Card,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  TextField,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { clampPercent, formatDate, getDeadlineStatus } from '../../utils/helpers'
import { STATUS_COLORS } from '../../constants/theme'
import { Stack } from './Stack'

export const StatusBadge = memo(function StatusBadge({ status }) {
  const key = String(status || 'pending').toLowerCase()
  const color = STATUS_COLORS[key] || 'default'
  return <Chip size="small" label={status || 'pending'} color={color} variant="filled" />
})

export const ProgressBar = memo(function ProgressBar({ value, label, showLabel = true }) {
  const pct = clampPercent(value)
  const theme = useTheme()
  const color =
    pct >= 80 ? theme.palette.success.main : pct >= 40 ? theme.palette.primary.main : theme.palette.warning.main

  return (
    <Box>
      {showLabel && (
        <Stack direction="row" justifyContent="space-between" mb={0.5}>
          <Typography variant="caption" color="text.secondary">
            {label || 'Progress'}
          </Typography>
          <Typography variant="caption" fontWeight={700}>
            {pct}%
          </Typography>
        </Stack>
      )}
      <LinearProgress
        variant="determinate"
        value={pct}
        sx={{
          bgcolor: alpha(color, 0.15),
          '& .MuiLinearProgress-bar': {
            bgcolor: color,
            borderRadius: 999,
            transition: 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
          },
        }}
      />
    </Box>
  )
})

export const ConfirmDialog = memo(function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onClose,
  loading,
  color = 'primary',
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle fontWeight={700}>{title}</DialogTitle>
      <DialogContent>
        <Typography color="text.secondary">{message}</Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          {cancelLabel}
        </Button>
        <Button variant="contained" color={color} onClick={onConfirm} disabled={loading}>
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
})

export const FormDialog = memo(function FormDialog({
  open,
  title,
  children,
  onClose,
  onSubmit,
  submitLabel = 'Save',
  loading,
  maxWidth = 'sm',
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth={maxWidth} fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography fontWeight={700}>{title}</Typography>
        <IconButton onClick={onClose} size="small" aria-label="Close dialog">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>{children}</DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="contained" onClick={onSubmit} disabled={loading}>
          {loading ? 'Saving…' : submitLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
})

export const MarkdownPanel = memo(function MarkdownPanel({ content, title }) {
  if (!content) return null
  return (
    <Box
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: 'action.hover',
        '& p': { m: 0, mb: 1 },
        '& ul': { pl: 2, m: 0 },
      }}
    >
      {title && (
        <Typography variant="subtitle2" fontWeight={700} mb={1}>
          {title}
        </Typography>
      )}
      {Array.isArray(content) ? (
        <Stack spacing={1}>
          {content.map((item, i) => (
            <Typography key={i} variant="body2" component="div">
              <ReactMarkdown>{String(item)}</ReactMarkdown>
            </Typography>
          ))}
        </Stack>
      ) : (
        <Typography variant="body2" component="div">
          <ReactMarkdown>{String(content)}</ReactMarkdown>
        </Typography>
      )}
    </Box>
  )
})

export const SearchField = memo(function SearchField({ value, onChange, placeholder = 'Search…' }) {
  return (
    <TextField
      size="small"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      fullWidth
      slotProps={{
        htmlInput: { 'aria-label': placeholder },
      }}
      sx={{ maxWidth: { sm: 320 } }}
    />
  )
})

export const DeadlineChip = memo(function DeadlineChip({ deadline }) {
  const status = getDeadlineStatus(deadline)
  const color = STATUS_COLORS[status] || 'default'
  return (
    <Chip
      size="small"
      variant="outlined"
      color={color}
      label={formatDate(deadline)}
    />
  )
})

export const AnimatedList = memo(function AnimatedList({ children }) {
  return (
    <AnimatePresence mode="popLayout">
      {children}
    </AnimatePresence>
  )
})

export const MotionCard = memo(function MotionCard({ children, ...props }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24 }}
      whileHover={{ y: -2 }}
      style={{ height: props.sx?.height === '100%' ? '100%' : undefined }}
    >
      <Card {...props}>{children}</Card>
    </motion.div>
  )
})
