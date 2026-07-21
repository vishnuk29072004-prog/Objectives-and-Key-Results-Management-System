import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Box, CssBaseline, Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Button } from '@mui/material';
import FlagIcon from '@mui/icons-material/Flag';
import ChecklistIcon from '@mui/icons-material/Checklist';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MenuIcon from '@mui/icons-material/Menu';
import ObjectiveForm from './components/ObjectiveForm';
import ObjectivesDashboard from './components/ObjectivesDashboard';
import TasksView from './components/TasksView';
import RemindersPanel from './components/RemindersPanel';
import CommonDashboard from './components/CommonDashboard';
import './config'; // Import API configuration

const drawerWidth = 220;

export default function App() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [panel, setPanel] = useState('common-dashboard'); // 'common-dashboard', 'objectives', 'create', 'reminders', 'tasks'
  const [refresh, setRefresh] = useState(false);
  const [selectedObjective, setSelectedObjective] = useState(null);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleCreated = () => {
    setPanel('common-dashboard');
    setRefresh((r) => !r);
  };

  const handleSelectObjective = (id) => {
    setSelectedObjective(id);
    setPanel('tasks');
  };

  const handleBackToObjectives = () => {
    setSelectedObjective(null);
    setPanel('objectives');
  };

  const handleNavigateToCreate = () => {
    setPanel('create');
  };

  const handleNavigateToReminders = () => {
    setPanel('reminders');
  };

  const handleNavigateToObjectives = () => {
    setPanel('objectives');
  };

  const drawer = (
    <div>
      <Toolbar />
      <List>
        <ListItem button key="Dashboard" onClick={() => { setPanel('common-dashboard'); setSelectedObjective(null); }}>
          <ListItemIcon><FlagIcon color="primary" /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button key="Objectives" onClick={() => { setPanel('objectives'); setSelectedObjective(null); }}>
          <ListItemIcon><ChecklistIcon color="primary" /></ListItemIcon>
          <ListItemText primary="Objectives" />
        </ListItem>
        <ListItem button key="Reminders" onClick={() => setPanel('reminders')}>
          <ListItemIcon><NotificationsIcon color="primary" /></ListItemIcon>
          <ListItemText primary="Reminders" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Viva Goals - OKR Tracker
          </Typography>
          {panel === 'common-dashboard' && (
            <Button color="inherit" onClick={() => setPanel('create')}>
              Add Objective
            </Button>
          )}
          {panel === 'objectives' && (
            <Button color="inherit" onClick={() => setPanel('create')}>
              Add Objective
            </Button>
          )}
          {panel === 'create' && (
            <Button color="inherit" onClick={() => setPanel('common-dashboard')}>
              Dashboard
            </Button>
          )}
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="mailbox folders"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
      >
        <Toolbar />
        {panel === 'tasks' && selectedObjective ? (
          <TasksView objectiveId={selectedObjective} onBack={handleBackToObjectives} />
        ) : panel === 'create' ? (
          <ObjectiveForm onCreated={handleCreated} />
        ) : panel === 'reminders' ? (
          <RemindersPanel />
        ) : panel === 'objectives' ? (
          <ObjectivesDashboard key={refresh} onSelectObjective={handleSelectObjective} />
        ) : (
          <CommonDashboard 
            onNavigateToCreate={handleNavigateToCreate}
            onNavigateToReminders={handleNavigateToReminders}
            onNavigateToObjectives={handleNavigateToObjectives}
          />
        )}
      </Box>
    </Box>
  );
} 