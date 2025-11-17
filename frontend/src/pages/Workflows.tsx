import React, { useEffect, useState } from 'react'
import { createWorkflow, getWorkflow, listExecutions, runWorkflow } from '../api/workflows'

export default function Workflows() {
  const [workflows, setWorkflows] = useState<any[]>([])
  const [name, setName] = useState('')

  async function create() {
    const res = await createWorkflow(name || 'New Workflow', { nodes: [], edges: [] })
    alert('Created workflow ' + res.id)
  }

  return (
    <div>
      <h2>Workflows</h2>
      <div>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Workflow name" />
        <button onClick={create}>Create</button>
      </div>
      <div>
        <p>List of workflows will appear here (not implemented).</p>
      </div>
    </div>
  )
}
