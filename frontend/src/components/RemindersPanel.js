import React, { useState, useEffect } from 'react';
import { Typography, Paper, Button, CircularProgress, Stack, Box } from '@mui/material';
import axios from 'axios';

export default function RemindersPanel() {
  const [loading, setLoading] = useState(false);
  const [reminders, setReminders] = useState([]);
  const [error, setError] = useState('');

  const fetchReminders = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get('/reminders/check/');
      setReminders(res.data.reminders || []);
      
      // Also fetch urgent items for better visibility
      try {
        const urgentRes = await axios.get('/api/dashboard/urgent-items');
        if (urgentRes.data.success) {
          const urgent = urgentRes.data.urgent_items;
          console.log('Urgent items:', urgent);
        }
      } catch (urgentError) {
        console.log('Could not fetch urgent items:', urgentError);
      }
    } catch (e) {
      setError('Failed to fetch reminders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  return (
    <Paper sx={{ p: 3, mb: 4, maxWidth: 600 }} elevation={3}>
      <Typography variant="h6" gutterBottom>
        Reminders & Notifications
      </Typography>
      <Stack spacing={2}>
        <Button variant="contained" onClick={fetchReminders} disabled={loading}>
          {loading ? <CircularProgress size={20} /> : 'Check for Reminders'}
        </Button>
        {reminders.length === 0 && !loading && <Typography>No reminders at this time.</Typography>}
        {reminders.map((rem, idx) => {
          // Calculate days until deadline
          const deadline = new Date(rem.deadline);
          const today = new Date();
          const daysUntil = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
          
          let urgencyColor = '#fffde7'; // Default light yellow
          let urgencyText = 'Due Soon';
          
          if (daysUntil < 0) {
            urgencyColor = '#ffebee'; // Light red for overdue
            urgencyText = `OVERDUE ${Math.abs(daysUntil)} days`;
          } else if (daysUntil === 0) {
            urgencyColor = '#ffcdd2'; // Darker red for due today
            urgencyText = 'DUE TODAY';
          } else if (daysUntil === 1) {
            urgencyColor = '#ffcdd2'; // Red for due tomorrow
            urgencyText = 'DUE TOMORROW';
          } else if (daysUntil <= 2) {
            urgencyColor = '#ffe0b2'; // Orange for due in 2 days
            urgencyText = `DUE IN ${daysUntil} DAYS`;
          }
          
          return (
            <Paper key={idx} sx={{ p: 2, background: urgencyColor, border: '1px solid #ddd' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: daysUntil <= 1 ? '#d32f2f' : '#f57c00' }}>
                ⚡ Subtask: {rem.name}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Deadline:</strong> {rem.deadline}
              </Typography>
              <Typography variant="body2" sx={{ color: daysUntil <= 1 ? '#d32f2f' : '#f57c00', fontWeight: 'bold' }}>
                Status: {urgencyText}
              </Typography>
              {rem.objective && (
                <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#666' }}>
                  From: {rem.objective}
                </Typography>
              )}
            </Paper>
          );
        })}
        
        {/* Show overdue items more prominently */}
        {reminders.length > 0 && (
          <Box mt={3}>
            <Typography variant="h6" color="error" gutterBottom>
              ⚠️ Overdue Items Summary
            </Typography>
            {reminders.filter(rem => {
              const deadline = new Date(rem.deadline);
              const today = new Date();
              const daysUntil = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
              return daysUntil < 0;
            }).map((overdue, idx) => (
              <Paper key={`overdue-${idx}`} sx={{ p: 2, background: '#ffebee', border: '2px solid #d32f2f', mb: 1 }}>
                <Typography variant="subtitle1" color="error" fontWeight="bold">
                  🚨 OVERDUE: {overdue.name}
                </Typography>
                <Typography variant="body2">
                  <strong>Deadline:</strong> {overdue.deadline}
                </Typography>
                <Typography variant="body2" color="error">
                  <strong>Days Overdue:</strong> {Math.abs(Math.ceil((new Date(overdue.deadline) - new Date()) / (1000 * 60 * 60 * 24)))} days
                </Typography>
              </Paper>
            ))}
          </Box>
        )}
        
        {error && <Typography color="error">{error}</Typography>}
      </Stack>
    </Paper>
  );
} 