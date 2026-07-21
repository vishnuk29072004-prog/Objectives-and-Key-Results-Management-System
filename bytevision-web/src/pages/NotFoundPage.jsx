import { Box, Button, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <Box
      component={motion.div}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      sx={{ py: 12, textAlign: 'center' }}
    >
      <Typography variant="h1" fontWeight={800} color="primary">
        404
      </Typography>
      <Typography variant="h5" fontWeight={700} mt={1}>
        Page not found
      </Typography>
      <Typography color="text.secondary" mt={1} mb={3}>
        This route does not exist in the byteVision frontend.
      </Typography>
      <Button variant="contained" onClick={() => navigate('/')}>
        Back to Dashboard
      </Button>
    </Box>
  )
}
