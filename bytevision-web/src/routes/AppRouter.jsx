import { lazy, Suspense } from 'react'
import { Navigate, useRoutes } from 'react-router-dom'
import { Box, CircularProgress } from '@mui/material'
import AppLayout from '../layouts/AppLayout'

const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const ObjectivesPage = lazy(() => import('../pages/ObjectivesPage'))
const TasksPage = lazy(() => import('../pages/TasksPage'))
const SubtasksPage = lazy(() => import('../pages/SubtasksPage'))
const RemindersPage = lazy(() => import('../pages/RemindersPage'))
const AnalyticsPage = lazy(() => import('../pages/AnalyticsPage'))
const AiInsightsPage = lazy(() => import('../pages/AiInsightsPage'))
const SettingsPage = lazy(() => import('../pages/SettingsPage'))
const ProfilePage = lazy(() => import('../pages/ProfilePage'))
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'))

function PageLoader() {
  return (
    <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 320 }}>
      <CircularProgress />
    </Box>
  )
}

export default function AppRouter() {
  return useRoutes([
    {
      path: '/',
      element: <AppLayout />,
      children: [
        {
          index: true,
          element: (
            <Suspense fallback={<PageLoader />}>
              <DashboardPage />
            </Suspense>
          ),
        },
        {
          path: 'objectives',
          element: (
            <Suspense fallback={<PageLoader />}>
              <ObjectivesPage />
            </Suspense>
          ),
        },
        {
          path: 'objectives/:id',
          element: (
            <Suspense fallback={<PageLoader />}>
              <TasksPage />
            </Suspense>
          ),
        },
        {
          path: 'tasks',
          element: (
            <Suspense fallback={<PageLoader />}>
              <TasksPage />
            </Suspense>
          ),
        },
        {
          path: 'subtasks',
          element: (
            <Suspense fallback={<PageLoader />}>
              <SubtasksPage />
            </Suspense>
          ),
        },
        {
          path: 'reminders',
          element: (
            <Suspense fallback={<PageLoader />}>
              <RemindersPage />
            </Suspense>
          ),
        },
        {
          path: 'analytics',
          element: (
            <Suspense fallback={<PageLoader />}>
              <AnalyticsPage />
            </Suspense>
          ),
        },
        {
          path: 'ai-insights',
          element: (
            <Suspense fallback={<PageLoader />}>
              <AiInsightsPage />
            </Suspense>
          ),
        },
        {
          path: 'settings',
          element: (
            <Suspense fallback={<PageLoader />}>
              <SettingsPage />
            </Suspense>
          ),
        },
        {
          path: 'profile',
          element: (
            <Suspense fallback={<PageLoader />}>
              <ProfilePage />
            </Suspense>
          ),
        },
        {
          path: '404',
          element: (
            <Suspense fallback={<PageLoader />}>
              <NotFoundPage />
            </Suspense>
          ),
        },
        { path: '*', element: <Navigate to="/404" replace /> },
      ],
    },
  ])
}
