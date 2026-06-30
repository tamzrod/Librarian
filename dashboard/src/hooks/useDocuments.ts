import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { DocumentListResponse, DocumentSummary } from '../types/api'

interface UseDocumentsResult {
  data: DocumentListResponse | null
  loading: boolean
  error: Error | null
  documents: DocumentSummary[]
  total: number
  refetch: () => void
}

export function useDocuments(
  params: { limit?: number; offset?: number; status?: string } = {},
  pollInterval?: number
): UseDocumentsResult {
  const [data, setData] = useState<DocumentListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      const result = await api.getDocuments({
        limit: params.limit || 50,
        offset: params.offset || 0,
        status: params.status,
      })
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch documents'))
    } finally {
      setLoading(false)
    }
  }, [params.limit, params.offset, params.status])

  useEffect(() => {
    fetchDocuments()
    
    if (pollInterval) {
      const interval = setInterval(fetchDocuments, pollInterval)
      return () => clearInterval(interval)
    }
  }, [fetchDocuments, pollInterval])

  return {
    data,
    loading,
    error,
    documents: data?.documents || [],
    total: data?.total || 0,
    refetch: fetchDocuments,
  }
}
