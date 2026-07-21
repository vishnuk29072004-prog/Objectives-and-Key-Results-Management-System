import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  LinearProgress, 
  Stack, 
  Button, 
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert
} from '@mui/material';
import {
  Flag as FlagIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Category as CategoryIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import axios from 'axios';

export default function CommonDashboard({ onNavigateToCreate, onNavigateToReminders, onNavigateToObjectives }) {
  const [overview, setOverview] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [urgentItems, setUrgentItems] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewRes, statsRes, urgentRes] = await Promise.all([
        axios.get('/api/dashboard/overview'),
        axios.get('/api/dashboard/statistics'),
        axios.get('/api/dashboard/urgent-items')
      ]);

      if (overviewRes.data.success) {
        setOverview(overviewRes.data.overview);
      }
      if (statsRes.data.success) {
        setStatistics(statsRes.data.statistics);
      }
      if (urgentRes.data.success) {
        setUrgentItems(urgentRes.data.urgent_items);
      }
    } catch (e) {
      setError('Failed to load dashboard data.');
      console.error('Dashboard data fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculateDeadlines = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/deadlines/recalculate');
      
      if (response.data.success) {
        // Refresh dashboard data after recalculation
        await fetchDashboardData();
        alert('Deadlines recalculated successfully!');
      } else {
        alert('Failed to recalculate deadlines: ' + response.data.error);
      }
    } catch (e) {
      alert('Error recalculating deadlines: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }



  const getUrgencyText = (days) => {
    if (days < 0) return `OVERDUE ${Math.abs(days)} days`;
    if (days === 0) return 'DUE TODAY';
    if (days === 1) return 'DUE TOMORROW';
    return `DUE IN ${days} DAYS`;
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold" color="primary">
          Dashboard Overview
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchDashboardData}
            size="small"
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={onNavigateToCreate}
            size="small"
          >
            Add Objective
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRecalculateDeadlines}
            size="small"
            color="secondary"
          >
            Recalculate Deadlines
          </Button>
        </Box>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <FlagIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" color="primary">
                  Total Objectives
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                {overview?.total_objectives || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {overview?.active_objectives || 0} Active, {overview?.completed_objectives || 0} Completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" color="success.main">
                  Overall Progress
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="success.main">
                {overview?.overall_progress || 0}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={overview?.overall_progress || 0} 
                sx={{ height: 8, borderRadius: 4, mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <WarningIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6" color="error.main">
                  Overdue Items
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="error.main">
                {overview?.overdue_count || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Require immediate attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <ScheduleIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6" color="warning.main">
                  Due Soon
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="warning.main">
                {overview?.due_soon_count || 0}
              </Typography>
                              <Typography variant="body2" color="text.secondary">
                  Due within 2 days
                </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics and Urgent Items */}
      <Grid container spacing={3}>
        {/* Statistics by Category */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center">
              <CategoryIcon sx={{ mr: 1 }} />
              Progress by Category
            </Typography>
            {statistics?.by_category ? (
              <Stack spacing={2}>
                {Object.entries(statistics.by_category).map(([category, stats]) => (
                  <Box key={category}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" fontWeight="medium">
                        {category}
                      </Typography>
                      <Typography variant="body2" color="primary">
                        {stats.progress}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={stats.progress} 
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {stats.count} objectives
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">No category data available</Typography>
            )}
          </Paper>
        </Grid>

        {/* Statistics by Owner */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center">
              <PersonIcon sx={{ mr: 1 }} />
              Progress by Owner
            </Typography>
            {statistics?.by_owner ? (
              <Stack spacing={2}>
                {Object.entries(statistics.by_owner).map(([owner, stats]) => (
                  <Box key={owner}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" fontWeight="medium">
                        {owner}
                      </Typography>
                      <Typography variant="body2" color="primary">
                        {stats.progress}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={stats.progress} 
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {stats.count} objectives
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">No owner data available</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Urgent Items Section */}
      <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" display="flex" alignItems="center">
            <NotificationsIcon sx={{ mr: 1 }} />
            Urgent Items Requiring Attention
          </Typography>
          <Button
            variant="outlined"
            startIcon={<NotificationsIcon />}
            onClick={onNavigateToReminders}
            size="small"
          >
            View All Reminders
          </Button>
        </Box>

        <Grid container spacing={3}>
          {/* Overdue Items */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" color="error" gutterBottom>
              ⚠️ Overdue Items
            </Typography>
            {urgentItems?.overdue_tasks?.length > 0 || urgentItems?.overdue_subtasks?.length > 0 ? (
              <List dense>
                {urgentItems.overdue_tasks.map((task) => (
                  <ListItem key={`task-${task.id}`} sx={{ pl: 0 }}>
                    <ListItemIcon>
                      <AssignmentIcon color="error" />
                    </ListItemIcon>
                    <ListItemText
                      primary={task.name}
                      secondary={`${task.objective_name} • ${getUrgencyText(-task.days_overdue)}`}
                    />
                    <Chip 
                      label={getUrgencyText(-task.days_overdue)} 
                      color="error" 
                      size="small" 
                    />
                  </ListItem>
                ))}
                {urgentItems.overdue_subtasks.map((subtask) => (
                  <ListItem key={`subtask-${subtask.id}`} sx={{ pl: 0 }}>
                    <ListItemIcon>
                      <CheckCircleIcon color="error" />
                    </ListItemIcon>
                    <ListItemText
                      primary={subtask.name}
                      secondary={`${subtask.task_name} • ${subtask.objective_name} • ${getUrgencyText(-subtask.days_overdue)}`}
                    />
                    <Chip 
                      label={getUrgencyText(-subtask.days_overdue)} 
                      color="error" 
                      size="small" 
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="success.main" variant="body2">
                ✅ No overdue items
              </Typography>
            )}
          </Grid>

          {/* Due Soon Items */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" color="warning.main" gutterBottom>
              ⏰ Due Soon (Next 2 Days)
            </Typography>
            {urgentItems?.due_soon_tasks?.length > 0 || urgentItems?.due_soon_subtasks?.length > 0 ? (
              <List dense>
                {urgentItems.due_soon_tasks.map((task) => (
                  <ListItem key={`task-soon-${task.id}`} sx={{ pl: 0 }}>
                    <ListItemIcon>
                      <AssignmentIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={task.name}
                      secondary={`${task.objective_name} • ${getUrgencyText(task.days_until)}`}
                    />
                    <Chip 
                      label={getUrgencyText(task.days_until)} 
                      color="warning" 
                      size="small" 
                    />
                  </ListItem>
                ))}
                {urgentItems.due_soon_subtasks.map((subtask) => (
                  <ListItem key={`subtask-soon-${subtask.id}`} sx={{ pl: 0 }}>
                    <ListItemIcon>
                      <CheckCircleIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={subtask.name}
                      secondary={`${subtask.task_name} • ${subtask.objective_name} • ${getUrgencyText(subtask.days_until)}`}
                    />
                    <Chip 
                      label={getUrgencyText(subtask.days_until)} 
                      color="warning" 
                      size="small" 
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="success.main" variant="body2">
                ✅ No items due soon
              </Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Quick Actions */}
      <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={onNavigateToCreate}
          >
            Create New Objective
          </Button>
          <Button
            variant="outlined"
            startIcon={<FlagIcon />}
            onClick={onNavigateToObjectives}
          >
            View All Objectives
          </Button>
          <Button
            variant="outlined"
            startIcon={<NotificationsIcon />}
            onClick={onNavigateToReminders}
          >
            Manage Reminders
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
