import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, LinearProgress, Stack, Button, CircularProgress } from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import AssessmentIcon from '@mui/icons-material/Assessment';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

export default function ObjectivesDashboard({ onSelectObjective }) {
  const [objectives, setObjectives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [aiRecs, setAiRecs] = useState({});
  const [aiSummaries, setAiSummaries] = useState({});
  const [loadingAI, setLoadingAI] = useState({}); // Track loading state per objective
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    const fetchObjectives = async () => {
      setLoading(true);
      setError('');
      try {
        // Placeholder: backend currently returns empty, so simulate
        const res = await axios.get('/api/objectives');
        setObjectives(res.data.objectives || []);
      } catch (e) {
        setError('Failed to load objectives.');
      } finally {
        setLoading(false);
      }
    };
    fetchObjectives();
  }, []);

  // Load AI data for a specific objective
  const loadAIData = async (objectiveId, type) => {
    try {
      setLoadingAI(prev => ({ ...prev, [objectiveId]: true }));
      
      if (type === 'summary' || type === 'both') {
        const sumRes = await axios.get(`/api/objectives/${objectiveId}/ai-summary`);
        const summary = sumRes.data.summary;
        console.log(`Summary for objective ${objectiveId}:`, summary, typeof summary);
        const sumText = Array.isArray(summary)
          ? summary.join('\n• ')
          : (summary || 'No summary available.');
        
        setAiSummaries(prev => ({ ...prev, [objectiveId]: sumText }));
      }
      
      if (type === 'recommendation' || type === 'both') {
        const recRes = await axios.get(`/api/objectives/${objectiveId}/ai-recommendation`);
        const recommendation = recRes.data.recommendation;
        console.log(`Recommendation for objective ${objectiveId}:`, recommendation, typeof recommendation);
        const recText = Array.isArray(recommendation) 
          ? recommendation.join('\n• ') 
          : (recommendation || 'No recommendation available.');
        
        setAiRecs(prev => ({ ...prev, [objectiveId]: recText }));
      }
    } catch (error) {
      console.error(`Error loading AI data for objective ${objectiveId}:`, error);
      if (type === 'summary' || type === 'both') {
        setAiSummaries(prev => ({ ...prev, [objectiveId]: 'No summary available.' }));
      }
      if (type === 'recommendation' || type === 'both') {
        setAiRecs(prev => ({ ...prev, [objectiveId]: 'No recommendation available.' }));
      }
    } finally {
      setLoadingAI(prev => ({ ...prev, [objectiveId]: false }));
    }
  };

  const toggleExpand = (id, section) => {
    setExpanded((prev) => ({
      ...prev,
      [id + '-' + section]: !prev[id + '-' + section],
    }));
  };

  // Utility function to safely get text content
  const getSafeText = (content) => {
    if (!content) return '';
    if (Array.isArray(content)) {
      return content.join('\n• ');
    }
    return String(content);
  };

  // Placeholder: show a message if no objectives
  if (loading) return <CircularProgress sx={{ mt: 4 }} />;
  if (error) return <Typography color="error">{error}</Typography>;
  if (!objectives.length) return <Typography sx={{ mt: 4 }}>No objectives found. Create one to get started!</Typography>;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Your Objectives
      </Typography>
      <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', px: { xs: 1, sm: 2 }, mt: { xs: 2, md: 6 } }}>
        <Stack spacing={4} sx={{ width: '100%', maxWidth: 700, mx: 'auto' }}>
          {objectives.map((obj) => (
            <Paper key={obj.id} sx={{ p: { xs: 2, sm: 3 }, mb: 3, width: '100%', maxWidth: 700, mx: 'auto', boxShadow: 2, borderRadius: 2, background: '#fff' }}>
              <Box sx={{ width: '100%', mb: 1 }}>
                <Typography variant="subtitle1" fontWeight={600}>{obj.objective}</Typography>
                <Typography variant="body2" color="text.secondary">Deadline: {obj.deadline}</Typography>
                <Typography variant="body2" color="text.secondary">Category: {obj.category || 'N/A'}</Typography>
                <Typography variant="body2" color="text.secondary">Owner: {obj.owner || 'N/A'}</Typography>
              </Box>
              <Box sx={{ width: '100%', mt: 1, mb: 1 }}>
                <Typography variant="caption">Progress</Typography>
                <LinearProgress variant="determinate" value={obj.progress || 0} sx={{ height: 8, borderRadius: 4, mb: 1 }} />
                <Typography variant="caption">{obj.progress || 0}%</Typography>
              </Box>
                             <Box sx={{ display: 'flex', gap: 1, my: 2, flexWrap: 'wrap' }}>
                 <Button variant="outlined" onClick={() => onSelectObjective(obj.id)} sx={{ minWidth: 140 }}>
                   View Details
                 </Button>
                 {(!aiSummaries[obj.id] || !aiRecs[obj.id]) && (
                   <Button 
                     variant="contained" 
                     size="small"
                     onClick={() => loadAIData(obj.id, 'both')}
                     disabled={loadingAI[obj.id]}
                     startIcon={loadingAI[obj.id] ? <CircularProgress size={14} /> : <AutoFixHighIcon />}
                     sx={{ textTransform: 'none' }}
                   >
                     {loadingAI[obj.id] ? 'Loading AI...' : 'Load AI Insights'}
                   </Button>
                 )}
               </Box>
              <Box sx={{
                background: '#f4f8fd',
                borderRadius: 2,
                p: 2,
                mt: 1,
                mb: 1,
                boxShadow: 1,
                minWidth: 220,
                width: '100%',
              }}>
                                 <Stack direction="row" spacing={1} alignItems="flex-start">
                   <AssessmentIcon color="primary" sx={{ mt: 0.5 }} />
                   <Box sx={{ flex: 1 }}>
                     <Typography variant="subtitle2" fontWeight="bold">AI Progress Summary</Typography>
                     {aiSummaries[obj.id] ? (
                       <>
                         {getSafeText(aiSummaries[obj.id]).trim() ? (
                           <ReactMarkdown children={
                             expanded[obj.id + '-summary'] || getSafeText(aiSummaries[obj.id]).length < 220
                               ? getSafeText(aiSummaries[obj.id]) || 'No summary available.'
                               : getSafeText(aiSummaries[obj.id]).slice(0, 220) + '...'
                           }/>
                         ) : (
                           <Typography variant="body2" color="text.secondary">
                             No summary available.
                           </Typography>
                         )}
                         {getSafeText(aiSummaries[obj.id]).length >= 220 && (
                           <Button
                             size="small"
                             onClick={() => toggleExpand(obj.id, 'summary')}
                             sx={{ textTransform: 'none', pl: 0 }}
                             endIcon={expanded[obj.id + '-summary'] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                           >
                             {expanded[obj.id + '-summary'] ? 'Show Less' : 'Show More'}
                           </Button>
                         )}
                       </>
                     ) : (
                       <Button
                         size="small"
                         variant="outlined"
                         onClick={() => loadAIData(obj.id, 'summary')}
                         disabled={loadingAI[obj.id]}
                         startIcon={loadingAI[obj.id] ? <CircularProgress size={14} /> : <AssessmentIcon />}
                         sx={{ textTransform: 'none', mt: 1 }}
                       >
                         {loadingAI[obj.id] ? 'Loading...' : 'Get AI Summary'}
                       </Button>
                     )}
                   </Box>
                 </Stack>
                                 <Stack direction="row" spacing={1} alignItems="flex-start" sx={{ mt: 2 }}>
                   <AutoFixHighIcon color="secondary" sx={{ mt: 0.5 }} />
                   <Box sx={{ flex: 1 }}>
                     <Typography variant="subtitle2" fontWeight="bold">AI Recommendation</Typography>
                     {aiRecs[obj.id] ? (
                       <>
                         {getSafeText(aiRecs[obj.id]).trim() ? (
                           <ReactMarkdown children={
                             expanded[obj.id + '-rec'] || getSafeText(aiRecs[obj.id]).length < 220
                               ? getSafeText(aiRecs[obj.id]) || 'No recommendation available.'
                               : getSafeText(aiRecs[obj.id]).slice(0, 220) + '...'
                           }/>
                         ) : (
                           <Typography variant="body2" color="text.secondary">
                             No recommendation available.
                           </Typography>
                         )}
                         {getSafeText(aiRecs[obj.id]).length >= 220 && (
                           <Button
                             size="small"
                             onClick={() => toggleExpand(obj.id, 'rec')}
                             sx={{ textTransform: 'none', pl: 0 }}
                             endIcon={expanded[obj.id + '-rec'] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                           >
                             {expanded[obj.id + '-rec'] ? 'Show Less' : 'Show More'}
                           </Button>
                         )}
                       </>
                     ) : (
                       <Button
                         size="small"
                         variant="outlined"
                         onClick={() => loadAIData(obj.id, 'recommendation')}
                         disabled={loadingAI[obj.id]}
                         startIcon={loadingAI[obj.id] ? <CircularProgress size={14} /> : <AutoFixHighIcon />}
                         sx={{ textTransform: 'none', mt: 1 }}
                       >
                         {loadingAI[obj.id] ? 'Loading...' : 'Get AI Recommendation'}
                       </Button>
                     )}
                   </Box>
                 </Stack>
              </Box>
            </Paper>
          ))}
        </Stack>
      </Box>
    </Box>
  );
} 