import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  Paper,
  Divider,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Autocomplete,
} from '@mui/material'
import {
  ArrowBack,
  Delete,
  Download,
  Edit,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { useGetCall } from '../hooks/useGetCall'
import { useDeleteCall } from '../hooks/useDeleteCall'
import { useExportCall } from '../hooks/useExportCall'
import { useUpdateCallTags } from '../hooks/useUpdateCallTags'

const CallDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<boolean>(false)
  const [editTagsDialogOpen, setEditTagsDialogOpen] = useState<boolean>(false)
  const [editedTags, setEditedTags] = useState<string[]>([])
  const [success, setSuccess] = useState<string | null>(null)

  const { data: call, isLoading: loading, error } = useGetCall(id)
  const { mutate: deleteCallMutation, error: deleteError } = useDeleteCall()
  const { mutate: exportCallMutation, error: exportError } = useExportCall()
  const { mutate: updateTagsMutation, error: updateTagsError } = useUpdateCallTags()

  const handleDelete = () => {
    if (!id) return

    deleteCallMutation(id, {
      onSuccess: () => {
        navigate('/')
      },
    })
    setDeleteDialogOpen(false)
  }

  const handleExport = () => {
    if (!id) return

    exportCallMutation(id, {
      onSuccess: () => {
        setSuccess('Call exported successfully')
        setTimeout(() => setSuccess(null), 3000)
      },
    })
  }

  const handleEditTags = () => {
    if (call) {
      setEditedTags([...call.tags])
      setEditTagsDialogOpen(true)
    }
  }

  const handleSaveTags = () => {
    if (!id) return

    updateTagsMutation(
      { id, tags: editedTags },
      {
        onSuccess: () => {
          setSuccess('Tags updated successfully')
          setEditTagsDialogOpen(false)
          setTimeout(() => setSuccess(null), 3000)
        },
      }
    )
  }

  if (loading) {
    return <LinearProgress />
  }

  if (error && !call) {
    return (
      <Box>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')} sx={{ mb: 2 }}>
          Back to List
        </Button>
        <Alert severity="error">{error.message}</Alert>
      </Box>
    )
  }

  if (!call) {
    return null
  }

  const displayError = deleteError?.message || exportError?.message || updateTagsError?.message

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')}>
          Back to List
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Download />} onClick={handleExport}>
            Export JSON
          </Button>
          <Button variant="outlined" startIcon={<Edit />} onClick={handleEditTags}>
            Edit Tags
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={() => setDeleteDialogOpen(true)}
          >
            Delete
          </Button>
        </Box>
      </Box>

      {displayError && (
        <Alert severity="error" onClose={() => {}} sx={{ mb: 2 }}>
          {displayError}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1976D2' }}>
            {call.filename}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Uploaded: {call.upload_timestamp
              ? format(new Date(call.upload_timestamp), 'PPp')
              : 'Unknown date'}
          </Typography>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Tags
            </Typography>
            {call.tags_override && (
              <Chip label="Overridden" size="small" color="warning" />
            )}
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
            {call.tags && call.tags.length > 0 ? (
              call.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  sx={{ bgcolor: '#E3F2FD', color: '#1976D2', fontWeight: 500 }}
                />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No tags assigned
              </Typography>
            )}
          </Box>

          {call.roles && Object.keys(call.roles).length > 0 && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Roles
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                {Object.entries(call.roles).map(([speaker, role]) => (
                  <Chip
                    key={speaker}
                    label={`${speaker}: ${role}`}
                    sx={{ bgcolor: '#F3E5F5', color: '#7B1FA2' }}
                  />
                ))}
              </Box>
            </>
          )}

          {call.emotions && call.emotions.length > 0 && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Emotions Detected
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                {call.emotions.map((emotion) => (
                  <Chip key={emotion} label={emotion} sx={{ bgcolor: '#FFF3E0', color: '#E65100' }} />
                ))}
              </Box>
            </>
          )}

          {call.intent && (
            <>
              <Divider sx={{ my: 3 }} />
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Intent:
                </Typography>
                <Chip label={call.intent} sx={{ bgcolor: '#E8F5E9', color: '#2E7D32', fontWeight: 600 }} />
              </Box>
            </>
          )}

          {call.mood && (
            <>
              <Divider sx={{ my: 3 }} />
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Mood:
                </Typography>
                <Chip
                  label={call.mood}
                  sx={{
                    bgcolor:
                      call.mood === 'positive'
                        ? '#E8F5E9'
                        : call.mood === 'negative'
                        ? '#FFEBEE'
                        : '#F5F5F5',
                    color:
                      call.mood === 'positive'
                        ? '#2E7D32'
                        : call.mood === 'negative'
                        ? '#C62828'
                        : '#616161',
                    fontWeight: 600,
                  }}
                />
              </Box>
            </>
          )}

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Summary
          </Typography>
          <Paper sx={{ p: 2, bgcolor: '#F5F5F5', mb: 3 }}>
            <Typography variant="body1">{call.summary || 'No summary available'}</Typography>
          </Paper>

          {call.insights && call.insights.length > 0 && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Key Insights
              </Typography>
              <Box sx={{ mb: 3 }}>
                {call.insights.map((insight, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 1, bgcolor: '#E3F2FD' }}>
                    <Typography variant="body2">• {insight}</Typography>
                  </Paper>
                ))}
              </Box>
            </>
          )}

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Transcript
          </Typography>
          <Paper
            sx={{
              p: 3,
              bgcolor: '#FAFAFA',
              maxHeight: 500,
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              lineHeight: 1.6,
            }}
          >
            <Typography
              component="pre"
              sx={{
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                margin: 0,
              }}
            >
              {call.transcript || 'No transcript available'}
            </Typography>
          </Paper>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Metadata
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2">
              <strong>File Path:</strong> {call.audio_file_path}
            </Typography>
            <Typography variant="body2">
              <strong>Call ID:</strong> {call.id}
            </Typography>
            {call.created_at && (
              <Typography variant="body2">
                <strong>Created:</strong> {format(new Date(call.created_at), 'PPp')}
              </Typography>
            )}
            {call.updated_at && (
              <Typography variant="body2">
                <strong>Updated:</strong> {format(new Date(call.updated_at), 'PPp')}
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      <Dialog open={editTagsDialogOpen} onClose={() => setEditTagsDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Tags</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Autocomplete
              multiple
              freeSolo
              options={[]}
              value={editedTags}
              onChange={(_, newValue) => setEditedTags(newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Tags"
                  placeholder="Add tags"
                  helperText="Press Enter to add a new tag"
                />
              )}
            />
            {call.tags_original && call.tags_original.length > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Original AI tags: {call.tags_original.join(', ')}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTagsDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveTags} variant="contained" sx={{ bgcolor: '#1976D2' }}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Call</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this call? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CallDetail
