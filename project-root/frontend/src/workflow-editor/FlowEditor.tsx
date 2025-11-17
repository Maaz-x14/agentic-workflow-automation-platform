import React, { useCallback } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'react-flow-renderer'

const initialNodes = [
  { id: '1', data: { label: 'LLM Node' }, position: { x: 50, y: 50 } },
  { id: '2', data: { label: 'RAG Node' }, position: { x: 250, y: 50 } },
]

const initialEdges = []

export default function FlowEditor() {
  const onNodesChange = useCallback(() => {}, [])
  const onEdgesChange = useCallback(() => {}, [])
  const onConnect = useCallback(() => {}, [])

  return (
    <ReactFlow nodes={initialNodes} edges={initialEdges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
      <MiniMap />
      <Controls />
      <Background gap={16} />
    </ReactFlow>
  )
}
