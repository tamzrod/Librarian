import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { DocumentJourneyResponse, ExtractionResultsResponse } from '../types/api'

interface UseDocumentJourneyResult {
  data: DocumentJourneyResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useDocumentJourney(documentId: number | null): UseDocumentJourneyResult {
  const [data, setData] = useState<DocumentJourneyResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchJourney = useCallback(async () => {
    if (documentId === null) {
      setData(null)
      return
    }

    setLoading(true)
    try {
      const result = await api.getDocumentJourney(documentId)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch document journey'))
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    fetchJourney()
  }, [fetchJourney])

  return { data, loading, error, refetch: fetchJourney }
}

interface UseExtractionsResult {
  data: ExtractionResultsResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useExtractions(documentId: number | null): UseExtractionsResult {
  const [data, setData] = useState<ExtractionResultsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchExtractions = useCallback(async () => {
    if (documentId === null) {
      setData(null)
      return
    }

    setLoading(true)
    try {
      const result = await api.getDocumentExtractions(documentId)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch extractions'))
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    fetchExtractions()
  }, [fetchExtractions])

  return { data, loading, error, refetch: fetchExtractions }
}
