import React, { useEffect, useState, useCallback } from 'react';
import { Box, Typography, Paper, LinearProgress, Stack, Button, CircularProgress, Chip, Divider, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import axios from 'axios';
import SubtaskActions from './SubtaskActions';

export default function TasksView({ objectiveId, onBack }) {
  const [tasks, setTasks] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewDialog, setViewDialog] = useState(false);
  const [viewContent, setViewContent] = useState('');
  const [viewTitle, setViewTitle] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [tasksRes, progressRes] = await Promise.all([
        axios.get(`/api/objectives/${objectiveId}/tasks`),
        axios.get(`/api/objectives/${objectiveId}/progress`),
      ]);
      setTasks(tasksRes.data.tasks || []);
      setProgress(progressRes.data.summary || null);
    } catch (e) {
      setError('Failed to load tasks.');
    } finally {
      setLoading(false);
    }
  }, [objectiveId]);

  useEffect(() => {
    fetchData();
  }, [objectiveId, fetchData]);

  if (loading) return <CircularProgress sx={{ mt: 4 }} />;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <Box>
      <Button variant="outlined" onClick={onBack} sx={{ mb: 2 }}>
        Back to Objectives
      </Button>
      <Typography variant="h6" gutterBottom>
        Tasks & Subtasks
      </Typography>
      {progress && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2">Objective Progress</Typography>
          <LinearProgress variant="determinate" value={progress.objectiveCompletion} sx={{ height: 8, borderRadius: 4, mb: 1 }} />
          <Typography variant="caption">{progress.objectiveCompletion}%</Typography>
        </Paper>
      )}
      <Stack spacing={3}>
        {tasks.map((task) => (
          <Paper key={task.id} sx={{ p: 2 }}>
            <Typography variant="subtitle1">{task.name}</Typography>
            <Typography variant="body2" color="text.secondary">Deadline: {task.deadline ? task.deadline : 'N/A'}</Typography>
            <Box sx={{ my: 1 }}>
              <LinearProgress variant="determinate" value={task.progress || 0} sx={{ height: 6, borderRadius: 3 }} />
              <Typography variant="caption">Task Progress: {task.progress || 0}%</Typography>
            </Box>
            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2">Subtasks</Typography>
            <Stack spacing={1}>
              {task.subtasks.map((sub) => {
                const hasContent = !!(sub.result || sub.ai_generated_result);
                return (
                  <Paper key={sub.id} sx={{ p: 1.5, background: sub.status === 'approved' ? '#e8f5e9' : sub.status === 'pending' ? '#fffde7' : '#f3e5f5' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography variant="body2">{sub.name}</Typography>
                        <Typography variant="caption" color="text.secondary">Deadline: {sub.deadline ? sub.deadline : 'N/A'}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, position: 'relative' }}>
                        {sub.status === 'approved' && (
                          <Chip label="Verified" color="success" size="small" sx={{ ml: 1, fontWeight: 'bold', fontSize: '0.85rem', borderRadius: 1 }} />
                        )}
                        {hasContent && (
                          <Button size="small" variant="outlined" onClick={() => {
                            setViewTitle(sub.name);
                            setViewContent(sub.result || sub.ai_generated_result);
                            setViewDialog(true);
                          }}>View</Button>
                        )}
                      </Box>
                    </Box>
                    {sub.comment && (
                      <Typography variant="caption" color="text.secondary">
                        Comment: {sub.comment}
                      </Typography>
                    )}
                    <SubtaskActions subtask={sub} onUpdate={fetchData} />
                  </Paper>
                );
              })}
            </Stack>
          </Paper>
        ))}
      </Stack>
      <Dialog open={viewDialog} onClose={() => setViewDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Subtask Content: {viewTitle}</DialogTitle>
        <DialogContent>
          <Typography sx={{ whiteSpace: 'pre-line' }}>{viewContent}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 