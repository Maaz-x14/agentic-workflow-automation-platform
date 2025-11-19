import React, { useCallback, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
} from 'reactflow'

// per your request: import '@xyflow/react' css (some environments use 'reactflow/dist/style.css')
// Importing the requested file path; if your environment doesn't have @xyflow/react installed this import may be harmless or you can change to 'reactflow/dist/style.css'
import '@xyflow/react/dist/style.css'
import 'reactflow/dist/style.css'
import './styles/index.css'

import AgentNode from './components/AgentNode'

const nodeTypes = {
  agent: AgentNode,
}

const initialNodes: Node[] = [
  {
    id: 'agent-1',
    type: 'agent',
    position: { x: 250, y: 250 },
    data: { goal: 'Research LangGraph and save a short summary.' },
  },
]

const initialEdges: Edge[] = []

export default function App() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes)
  const [edges, setEdges] = useState<Edge[]>(initialEdges)

  const onConnect = useCallback((params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)), [])

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={(changes) => {}}
          onEdgesChange={(changes) => {}}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background gap={16} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}