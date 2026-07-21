import React, { useState } from 'react';
import { Box, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Typography, Stack } from '@mui/material';
import axios from 'axios';

export default function SubtaskActions({ subtask, onUpdate }) {
  const [openDialog, setOpenDialog] = useState(false);
  const [action, setAction] = useState(''); // 'update', 'ai-generate', 'review', 'edit'
  const [result, setResult] = useState('');
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiResult, setAiResult] = useState(subtask.result || subtask.ai_generated_result || '');

  const handleAction = async () => {
    setLoading(true);
    setError('');
    try {
      if (action === 'update') {
        await axios.post(`/api/subtasks/${subtask.id}/update`, { result, comment });
      } else if (action === 'ai-generate') {
        const res = await axios.post(`/api/subtasks/${subtask.id}/ai-generate`);
        setAiResult(res.data.result);
        setResult(res.data.result);
        return; // Don't close dialog, show AI result
      } else if (action === 'review') {
        await axios.post(`/api/subtasks/${subtask.id}/review`, { status: 'approved' });
      } else if (action === 'edit') {
        await axios.post(`/api/subtasks/${subtask.id}/edit`, { result });
      }
      setOpenDialog(false);
      setResult('');
      setComment('');
      if (onUpdate) onUpdate();
    } catch (e) {
      setError('Action failed.');
    } finally {
      setLoading(false);
    }
  };

  const openActionDialog = (actionType) => {
    setAction(actionType);
    setResult('');
    setComment('');
    setError('');
    if (actionType === 'ai-generate') {
      setResult(aiResult || '');
    }
    setOpenDialog(true);
  };

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        <Button size="small" variant="outlined" onClick={() => openActionDialog('update')}>
          Update
        </Button>
        <Button size="small" variant="outlined" onClick={() => openActionDialog('ai-generate')}>
          AI Generate
        </Button>
        <Button size="small" variant="outlined" onClick={() => openActionDialog('review')}>
          Review
        </Button>
        <Button size="small" variant="outlined" onClick={() => openActionDialog('edit')}>
          Edit
        </Button>
      </Stack>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {action === 'update' && 'Update Subtask'}
          {action === 'ai-generate' && 'AI Generate Result'}
          {action === 'review' && 'Review Subtask'}
          {action === 'edit' && 'Edit Result'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {action === 'update' && (
              <>
                <TextField
                  label="Result"
                  value={result}
                  onChange={(e) => setResult(e.target.value)}
                  multiline
                  rows={3}
                  fullWidth
                />
                <TextField
                  label="Comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  fullWidth
                />
              </>
            )}
            {action === 'ai-generate' && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  AI will generate a result for: {subtask.name}
                </Typography>
                {aiResult && (
                  <TextField
                    label="AI Generated Result"
                    value={aiResult}
                    onChange={(e) => setAiResult(e.target.value)}
                    multiline
                    rows={4}
                    fullWidth
                    sx={{ mt: 2 }}
                  />
                )}
                <Button
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={async () => {
                    setResult(aiResult);
                    setLoading(true);
                    setError('');
                    try {
                      await axios.post(`/api/subtasks/${subtask.id}/update`, { result: aiResult, comment: '' });
                      setOpenDialog(false);
                      setResult('');
                      setComment('');
                      if (onUpdate) onUpdate();
                    } catch (e) {
                      setError('Action failed.');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={!aiResult || loading}
                >
                  {loading ? 'Processing...' : 'Accept AI Result'}
                </Button>
              </Box>
            )}
            {action === 'review' && (
              <Box>
                <Typography>
                  Approve this subtask: <strong>{subtask.name}</strong>
                </Typography>
                {subtask.ai_generated_result && (
                  <TextField
                    label="AI Generated Result"
                    value={subtask.ai_generated_result}
                    multiline
                    rows={4}
                    fullWidth
                    sx={{ mt: 2 }}
                    InputProps={{ readOnly: true }}
                  />
                )}
              </Box>
            )}
            {action === 'edit' && (
              <Box>
                {subtask.ai_generated_result && (
                  <TextField
                    label="AI Generated Result"
                    value={subtask.ai_generated_result}
                    multiline
                    rows={4}
                    fullWidth
                    sx={{ mb: 2 }}
                    InputProps={{ readOnly: true }}
                  />
                )}
                <TextField
                  label="Manual Result"
                  value={result}
                  onChange={(e) => setResult(e.target.value)}
                  multiline
                  rows={4}
                  fullWidth
                />
              </Box>
            )}
            {error && <Typography color="error">{error}</Typography>}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleAction} variant="contained" disabled={loading}>
            {loading ? 'Processing...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
} 