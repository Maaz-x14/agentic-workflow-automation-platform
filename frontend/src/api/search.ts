import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function search(query: string, limit = 5) {
  const res = await api.get('/search', { params: { q: query, limit } })
  return res.data
}
