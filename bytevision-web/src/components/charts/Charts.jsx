import { memo } from 'react'
import { Box, Card, CardContent, Typography, useTheme } from '@mui/material'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import { COLORS } from '../../constants/theme'

const CHART_COLORS = [COLORS.primary, COLORS.secondary, COLORS.success, COLORS.warning, COLORS.danger, '#8B5CF6', '#06B6D4']

export const ChartCard = memo(function ChartCard({ title, subtitle, children, height = 280 }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" fontWeight={700}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" display="block" mb={2}>
            {subtitle}
          </Typography>
        )}
        <Box sx={{ width: '100%', height }}>{children}</Box>
      </CardContent>
    </Card>
  )
})

export const DonutChart = memo(function DonutChart({ data, dataKey = 'value', nameKey = 'name' }) {
  const theme = useTheme()
  if (!data?.length) return null
  return (
    <ResponsiveContainer>
      <PieChart>
        <Pie
          data={data}
          dataKey={dataKey}
          nameKey={nameKey}
          innerRadius={60}
          outerRadius={90}
          paddingAngle={3}
          stroke="none"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.paper,
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
})

export const SimpleBarChart = memo(function SimpleBarChart({ data, xKey = 'name', yKey = 'value', color = COLORS.primary }) {
  const theme = useTheme()
  if (!data?.length) return null
  return (
    <ResponsiveContainer>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.paper,
          }}
        />
        <Bar dataKey={yKey} fill={color} radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
})

export const SimpleLineChart = memo(function SimpleLineChart({ data, xKey = 'name', lines = [{ key: 'value', color: COLORS.primary }] }) {
  const theme = useTheme()
  if (!data?.length) return null
  return (
    <ResponsiveContainer>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.paper,
          }}
        />
        <Legend />
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            stroke={l.color}
            strokeWidth={2.5}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
})

export { CHART_COLORS }
