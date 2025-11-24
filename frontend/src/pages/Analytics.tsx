import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material'
import {
  PhoneCallback,
  Label,
  Description,
  TrendingUp,
} from '@mui/icons-material'
import { useGetAnalytics } from '../hooks/useGetAnalytics'

const Analytics = () => {
  const { data: analytics, isLoading: loading, error } = useGetAnalytics()

  if (loading) {
    return <LinearProgress />
  }

  if (error) {
    return <Alert severity="error">{error.message}</Alert>
  }

  if (!analytics) {
    return <Alert severity="info">No analytics data available</Alert>
  }

  const stats = [
    {
      title: 'Total Calls',
      value: analytics.total_calls,
      icon: PhoneCallback,
      color: '#1976D2',
    },
    {
      title: 'Total Tags',
      value: analytics.total_tags,
      icon: Label,
      color: '#42A5F5',
    },
    {
      title: 'Avg Tags/Call',
      value: analytics.average_tags_per_call.toFixed(2),
      icon: TrendingUp,
      color: '#64B5F6',
    },
    {
      title: 'With Transcript',
      value: analytics.calls_with_transcript,
      icon: Description,
      color: '#90CAF9',
    },
  ]

  const tagDistribution = Object.entries(analytics.tag_distribution || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ fontWeight: 600, color: '#1976D2', mb: 4 }}>
        Analytics
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Grid item xs={12} sm={6} md={3} key={stat.title}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        bgcolor: stat.color,
                        borderRadius: '50%',
                        p: 1.5,
                        mr: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Icon sx={{ color: 'white' }} />
                    </Box>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 600 }}>
                        {stat.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {stat.title}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Calls Status
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">With Transcript</Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {analytics.calls_with_transcript}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Without Transcript</Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {analytics.calls_without_transcript}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Top Tags
              </Typography>
              <List>
                {tagDistribution.length > 0 ? (
                  tagDistribution.map(([tag, count], index) => (
                    <ListItem key={tag}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              label={`#${index + 1}`}
                              size="small"
                              sx={{ bgcolor: '#E3F2FD', color: '#1976D2', fontWeight: 600 }}
                            />
                            <Typography variant="body1">{tag}</Typography>
                          </Box>
                        }
                        secondary={`${count} calls`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                    No tags available
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Analytics

