import React from 'react'

export default function NodePalette({ onAdd }: { onAdd?: (type: string) => void }) {
  return (
    <div className="node-palette">
      <h4>Nodes</h4>
      <button onClick={() => onAdd && onAdd('llm_node')}>Add LLM Node</button>
      <button onClick={() => onAdd && onAdd('rag_node')}>Add RAG Node</button>
      <button onClick={() => onAdd && onAdd('action_node')}>Add Action Node</button>
    </div>
  )
}
