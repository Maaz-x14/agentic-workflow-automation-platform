import React, { useEffect, useState } from 'react'
import { getExecution } from '../api/workflows'

export default function ExecutionView({ execId }: { execId: number }) {
  const [exec, setExec] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    async function fetch() {
      setLoading(true)
      const res = await getExecution(execId)
      if (mounted) setExec(res)
      setLoading(false)
    }
    fetch()
    const t = setInterval(fetch, 2000)
    return () => {
      mounted = false
      clearInterval(t)
    }
  }, [execId])

  if (loading) return <div>Loading execution...</div>
  if (!exec) return <div>No execution found</div>

  return (
    <div>
      <h3>Execution {exec.execution_id}</h3>
      <div>Status: {exec.status}</div>
      <div>
        {exec.steps.map((s: any) => (
          <div key={s.id} style={{ border: '1px solid #eee', margin: 8, padding: 8 }}>
            <div><strong>Node:</strong> {s.node_id} ({s.node_type})</div>
            <div><strong>Input:</strong> <pre>{JSON.stringify(s.input, null, 2)}</pre></div>
            <div><strong>Output:</strong> <pre>{JSON.stringify(s.output, null, 2)}</pre></div>
            <div><small>{s.timestamp}</small></div>
          </div>
        ))}
      </div>
    </div>
  )
}
