import { useState, useEffect, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Alert,
  Grid,
  Paper,
} from '@mui/material'
import {
  Upload,
  Delete,
  Visibility,
  Download,
  FilterList,
  DateRange,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { useGetCalls } from '../hooks/useGetCalls'
import { useUploadCall } from '../hooks/useUploadCall'
import { useDeleteCall } from '../hooks/useDeleteCall'
import { useExportCall } from '../hooks/useExportCall'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs from 'dayjs'

const CallsList = () => {
  const [selectedTag, setSelectedTag] = useState<string>('')
  const [startDate, setStartDate] = useState<dayjs.Dayjs | null>(null)
  const [endDate, setEndDate] = useState<dayjs.Dayjs | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState<boolean>(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [allTags, setAllTags] = useState<string[]>([])
  const navigate = useNavigate()

  const params: any = {}
  if (selectedTag) params.tag = selectedTag
  if (startDate) params.start_date = startDate.toISOString()
  if (endDate) params.end_date = endDate.toISOString()

  const { data: calls = [], isLoading: loading, error, refetch } = useGetCalls(params)
  const { mutate: uploadCall, isPending: uploading, error: uploadError } = useUploadCall()
  const { mutate: deleteCallMutation, error: deleteError } = useDeleteCall()
  const { mutate: exportCallMutation, error: exportError } = useExportCall()

  useEffect(() => {
    // Extract all unique tags
    const tags = new Set<string>()
    calls.forEach((call) => {
      call.tags?.forEach((tag) => tags.add(tag))
    })
    setAllTags(Array.from(tags).sort())
  }, [calls])

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      const allowedTypes = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!fileExt || !allowedTypes.includes(fileExt)) {
        setSuccess(null)
        return
      }
      // Validate file size (100MB)
      if (file.size > 100 * 1024 * 1024) {
        setSuccess(null)
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUpload = () => {
    if (!selectedFile) {
      return
    }

    setSuccess('Uploading and processing call... This may take a few moments.')
    uploadCall(selectedFile, {
      onSuccess: () => {
        setSuccess('Call uploaded and processed successfully!')
        setUploadDialogOpen(false)
        setSelectedFile(null)
        refetch()
        setTimeout(() => setSuccess(null), 5000)
      },
      onError: (error: Error) => {
        setSuccess(null)
      },
    })
  }

  const handleDelete = (id: string) => {
    if (!window.confirm('Are you sure you want to delete this call?')) {
      return
    }

    deleteCallMutation(id, {
      onSuccess: () => {
        setSuccess('Call deleted successfully')
        refetch()
        setTimeout(() => setSuccess(null), 3000)
      },
    })
  }

  const handleExport = (id: string) => {
    exportCallMutation(id, {
      onSuccess: () => {
        setSuccess('Call exported successfully')
        setTimeout(() => setSuccess(null), 3000)
      },
    })
  }

  const displayError = error?.message || uploadError?.message || deleteError?.message || exportError?.message

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600, color: '#1976D2' }}>
          Call Records
        </Typography>
        <Button
          variant="contained"
          startIcon={<Upload />}
          onClick={() => setUploadDialogOpen(true)}
          sx={{ bgcolor: '#1976D2' }}
        >
          Upload Call
        </Button>
      </Box>

      {displayError && (
        <Alert severity="error" onClose={() => { }} sx={{ mb: 2 }}>
          {displayError}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FilterList color="action" />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Tag</InputLabel>
            <Select
              value={selectedTag}
              label="Filter by Tag"
              onChange={(e) => setSelectedTag(e.target.value)}
            >
              <MenuItem value="">All Tags</MenuItem>
              {allTags.map((tag) => (
                <MenuItem key={tag} value={tag}>
                  {tag}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={(newValue) => setStartDate(newValue)}
              slotProps={{ textField: { size: 'small', sx: { width: 180 } } }}
            />
            <DatePicker
              label="End Date"
              value={endDate}
              onChange={(newValue) => setEndDate(newValue)}
              slotProps={{ textField: { size: 'small', sx: { width: 180 } } }}
            />
          </LocalizationProvider>
          {(selectedTag || startDate || endDate) && (
            <Button
              size="small"
              onClick={() => {
                setSelectedTag('')
                setStartDate(null)
                setEndDate(null)
              }}
              variant="outlined"
            >
              Clear Filters
            </Button>
          )}
        </Box>
      </Paper>

      {loading ? (
        <LinearProgress />
      ) : calls.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" align="center" color="text.secondary">
              No calls found. Upload a call to get started.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {calls.map((call) => (
            <Grid item xs={12} md={6} lg={4} key={call.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" gutterBottom noWrap>
                    {call.filename}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 2, minHeight: 40 }}
                  >
                    {call.summary || 'No summary available'}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                    {call.tags?.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        sx={{ bgcolor: '#E3F2FD', color: '#1976D2' }}
                      />
                    ))}
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {call.upload_timestamp
                      ? format(new Date(call.upload_timestamp), 'PPp')
                      : 'Unknown date'}
                  </Typography>
                </CardContent>
                <Box sx={{ p: 2, pt: 0, display: 'flex', gap: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<Visibility />}
                    onClick={() => navigate(`/calls/${call.id}`)}
                  >
                    View
                  </Button>
                  <IconButton
                    size="small"
                    onClick={() => handleExport(call.id)}
                    color="primary"
                  >
                    <Download fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(call.id)}
                    color="error"
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Call</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <input
              accept=".wav,.mp3,.m4a,.ogg,.flac,.webm"
              style={{ display: 'none' }}
              id="file-upload"
              type="file"
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload">
              <Button variant="outlined" component="span" fullWidth>
                {selectedFile ? selectedFile.name : 'Select Audio File'}
              </Button>
            </label>
            {selectedFile && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={!selectedFile || uploading}
            sx={{ bgcolor: '#1976D2' }}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CallsList

