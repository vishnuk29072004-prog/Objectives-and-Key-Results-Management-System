import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress, Stack, Tooltip, IconButton } from '@mui/material';
import axios from 'axios';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';

export default function ObjectiveForm({ onCreated }) {
  const [objective, setObjective] = useState('');
  const [deadline, setDeadline] = useState('');
  const [category, setCategory] = useState('');
  const [owner, setOwner] = useState('');
  const [requiredInputs, setRequiredInputs] = useState([]);
  const [inputs, setInputs] = useState({});
  const [loadingInputs, setLoadingInputs] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);

  const handleFetchInputs = async () => {
    setLoadingInputs(true);
    setError('');
    try {
      const res = await axios.post('/api/required-inputs', { objective });
      setRequiredInputs(res.data.inputs || []);
    } catch (e) {
      setError('Failed to fetch required inputs.');
    } finally {
      setLoadingInputs(false);
    }
  };

  const handleInputChange = (key, value) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const fetchObjectiveSuggestion = useCallback(async (text) => {
    if (!text) { setAiSuggestion(''); return; }
    setLoadingSuggestion(true);
    try {
      const res = await axios.post('/api/objective-suggestion', { objective: text });
      // Ignore stale responses if the user kept typing
      if (text !== objective) return;
      setAiSuggestion(res.data.suggestion || '');
    } catch (e) {
      setAiSuggestion('');
    } finally {
      setLoadingSuggestion(false);
    }
  }, [objective]);

  // Debounce objective suggestion calls until user stops typing for ~1.2s
  useEffect(() => {
    const trimmed = (objective || '').trim();
    if (!trimmed) {
      setAiSuggestion('');
      return;
    }
    const handle = setTimeout(() => {
      fetchObjectiveSuggestion(trimmed);
    }, 1200);
    return () => clearTimeout(handle);
  }, [objective, fetchObjectiveSuggestion]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await axios.post('/api/objectives', {
        objective,
        deadline,
        category,
        owner,
        inputs,
      });
      setObjective('');
      setDeadline('');
      setCategory('');
      setOwner('');
      setInputs({});
      setRequiredInputs([]);
      if (onCreated) onCreated();
    } catch (e) {
      setError('Failed to create objective.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 4, maxWidth: 600 }} elevation={3}>
      <Typography variant="h6" gutterBottom>
        Create New Objective
      </Typography>
      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            label="Objective"
            value={objective}
            onChange={(e) => {
              setObjective(e.target.value);
            }}
            required
            fullWidth
            InputProps={{
              endAdornment: loadingSuggestion ? <CircularProgress size={16} /> : aiSuggestion && (
                <Tooltip title="Use AI suggestion">
                  <IconButton size="small" onClick={() => setObjective(aiSuggestion)}>
                    <AutoFixHighIcon color="secondary" />
                  </IconButton>
                </Tooltip>
              )
            }}
          />
          {aiSuggestion && aiSuggestion !== objective && (
            <Typography variant="caption" color="secondary" sx={{ ml: 1 }}>
              AI Suggestion: {aiSuggestion}
            </Typography>
          )}
          <TextField
            label="Deadline"
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
          />
          <TextField
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            fullWidth
          />
          <TextField
            label="Owner"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            fullWidth
          />
          {requiredInputs.length > 0 && (
            <Box>
              <Typography variant="subtitle1" sx={{ mt: 2 }}>
                Required Inputs
              </Typography>
              {requiredInputs.map((input) => (
                <TextField
                  key={input}
                  label={input}
                  value={inputs[input] || ''}
                  onChange={(e) => handleInputChange(input, e.target.value)}
                  required
                  fullWidth
                  sx={{ mt: 1 }}
                />
              ))}
            </Box>
          )}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button
              variant="outlined"
              onClick={handleFetchInputs}
              disabled={!objective || loadingInputs}
            >
              {loadingInputs ? <CircularProgress size={20} /> : 'Fetch Required Inputs'}
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={submitting || !objective || !deadline || (requiredInputs.length > 0 && requiredInputs.some((i) => !inputs[i]))}
            >
              {submitting ? <CircularProgress size={20} /> : 'Create Objective'}
            </Button>
          </Box>
          {error && <Typography color="error">{error}</Typography>}
        </Stack>
      </Box>
    </Paper>
  );
} 