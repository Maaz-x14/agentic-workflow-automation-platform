import React, { useCallback, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap, addEdge, Connection, Edge, Node } from 'react-flow-renderer'
import NodePalette from './NodePalette'

const initialNodes: Node[] = [
  { id: '1', data: { label: 'LLM Node', nodeType: 'llm_node', prompt: 'Hello' }, position: { x: 50, y: 50 } },
  { id: '2', data: { label: 'RAG Node', nodeType: 'rag_node', query: 'Find me info' }, position: { x: 250, y: 50 } },
]

const initialEdges: Edge[] = []

export default function FlowEditor() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes)
  const [edges, setEdges] = useState<Edge[]>(initialEdges)

  const onNodesChange = useCallback((changes) => {
    // naive: accept external changes
  }, [])
  const onEdgesChange = useCallback((changes) => {}, [])
  const onConnect = useCallback((params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)), [])

  const addNode = (type: string) => {
    const id = String(Date.now())
    const n: Node = { id, data: { label: `${type}`, nodeType: type }, position: { x: 100, y: 200 } }
    setNodes((s) => [...s, n])
  }

  return (
    <div className="flow-root">
      <NodePalette onAdd={addNode} />
      <div className="flow-area">
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
          <MiniMap />
          <Controls />
          <Background gap={16} />
        </ReactFlow>
      </div>
    </div>
  )
}
