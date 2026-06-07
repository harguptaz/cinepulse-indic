// services/api.js
// Central API client for all backend communication

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ── Analysis endpoints ────────────────────────────────────────

export const fetchOverview = () =>
  api.get('/overview').then(r => r.data)

export const fetchTimeline = () =>
  api.get('/timeline').then(r => r.data)

export const fetchReportData = () =>
  api.get('/report-data').then(r => r.data)

export const fetchPipelineStatus = () =>
  api.get('/status').then(r => r.data)

// ── Comment endpoints ─────────────────────────────────────────

export const fetchComments = (params = {}) =>
  api.get('/comments', { params }).then(r => r.data)

export const fetchCommentStats = () =>
  api.get('/comments/stats').then(r => r.data)

// ── Report download ───────────────────────────────────────────

export const downloadReport = () => {
  window.open('/api/report/download', '_blank')
}

export default api
