/** Turn FastAPI error payloads into a readable string. */
export function formatApiError(err) {
  const detail = err?.response?.data?.detail
  if (!detail) {
    return err?.message || 'Something went wrong'
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('. ')
  }
  if (typeof detail === 'object') {
    return detail.msg || JSON.stringify(detail)
  }
  return String(detail)
}
