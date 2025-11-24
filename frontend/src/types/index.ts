export interface Call {
  id: string
  filename: string
  audio_file_path: string
  transcript: string
  summary: string
  tags: string[]
  tags_original?: string[]
  tags_override?: string[] | null
  roles?: Record<string, string>
  emotions?: string[]
  intent?: string
  mood?: string
  insights?: string[]
  upload_timestamp: string
  created_at: string
  updated_at: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
  count?: number
  limit?: number
  skip?: number
}

export interface Analytics {
  total_calls: number
  total_tags: number
  average_tags_per_call: number
  calls_with_transcript: number
  calls_without_transcript: number
  tag_distribution: Record<string, number>
}

export interface CallsParams {
  tag?: string
  start_date?: string
  end_date?: string
  limit?: number
  skip?: number
}
