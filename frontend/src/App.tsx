import React, { useCallback, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  ReactFlowProvider,
  useReactFlow, // We need this hook
  Node
} from '@xyflow/react'; // <--- EVERYTHING from @xyflow/react

import '@xyflow/react/dist/style.css';
import './styles/index.css';

import AgentNode from './components/AgentNode';

const nodeTypes = {
  agent: AgentNode,
};

const initialNodes: Node[] = [
  {
    id: 'agent-1',
    type: 'agent',
    position: { x: 250, y: 250 },
    data: { label: 'Agent-1', goal: '' },
  },
];

const initialEdges: Edge[] = [];

function Flow() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [loading, setLoading] = useState(false);
  
  // Use the hook to interact with the internal store
  const { getNodes, getEdges } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const runWorkflow = async () => {
    setLoading(true);
    
    // CRITICAL FIX: Get the *latest* state from the store, 
    // ignoring the potentially stale local 'nodes' state.
    const currentNodes = getNodes();
    const currentEdges = getEdges();

    const payload = { nodes: currentNodes, edges: currentEdges };
    console.log('🚀 Sending Fresh Payload:', payload);

    try {
      const res = await fetch('http://127.0.0.1:8000/workflow/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      console.log('✅ Workflow response:', data);
      alert('Workflow run complete!');
    } catch (err) {
      console.error('❌ Run failed', err);
      alert('Workflow run failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      {/* Top Bar */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, height: 64, zIndex: 10, background: '#0f172a', display: 'flex', alignItems: 'center', padding: '0 20px', justifyContent: 'space-between' }}>
        <h1 style={{ color: 'white', fontWeight: 'bold' }}>Agentic Workflow</h1>
        <button
          onClick={runWorkflow}
          disabled={loading}
          style={{
            background: loading ? '#4b5563' : '#10b981',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '6px',
            fontWeight: 'bold',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s'
          }}
        >
          {loading ? 'Running...' : 'Run Workflow'}
        </button>
      </div>

      <div style={{ paddingTop: 64, height: '100vh' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background gap={16} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <Flow />
    </ReactFlowProvider>
  );
}