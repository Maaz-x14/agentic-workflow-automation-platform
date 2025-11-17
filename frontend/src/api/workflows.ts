import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function createWorkflow(name: string, graph_json: any) {
  const res = await api.post('/workflow/', { name, graph_json })
  return res.data
}

export async function getWorkflow(id: number) {
  const res = await api.get(`/workflow/${id}`)
  return res.data
}

export async function runWorkflow(id: number) {
  const res = await api.post(`/workflow/run/${id}`)
  return res.data
}

export async function getExecution(id: number) {
  const res = await api.get(`/workflow/execution/${id}`)
  return res.data
}

export async function listExecutions(workflowId: number) {
  const res = await api.get(`/workflow/${workflowId}/executions`)
  return res.data
}
