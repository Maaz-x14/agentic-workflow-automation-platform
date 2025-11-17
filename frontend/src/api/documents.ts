import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function uploadDocuments(files: File[]) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const res = await api.post('/documents/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  return res.data
}
