import React, { useCallback, useState, useRef } from 'react';
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
  useReactFlow,
  Node,
} from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import './styles/index.css';

import AgentNode from './components/AgentNode';
import Sidebar from './components/Sidebar';

const nodeTypes = { agent: AgentNode };

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

  // 1. Use screenToFlowPosition instead of project
  const { getNodes, getEdges, screenToFlowPosition } = useReactFlow();

  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const runWorkflow = async () => {
    setLoading(true);
    try {
      // Always fetch fresh state from the store
      const currentNodes = getNodes();
      const currentEdges = getEdges();
      const payload = { nodes: currentNodes, edges: currentEdges };

      console.log('🚀 Sending Payload:', payload);

      const res = await fetch('http://127.0.0.1:8000/workflow/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      console.log('✅ Workflow response:', data);

      // If the backend returned per-node run status, update node data with previews
      const nodeRuns = data?.node_runs || [];
      if (Array.isArray(nodeRuns) && nodeRuns.length > 0) {
        setNodes((nds) =>
          nds.map((n) => {
            const nr = nodeRuns.find((r: any) => r.node_id === n.id);
            if (nr) {
              // Prefer full result from `results` if available
              const fullRes = data?.results?.[n.id]?.result ?? data?.results?.[n.id];
              return {
                ...n,
                data: {
                  ...n.data,
                  result: fullRes ?? nr.output_preview,
                  _run_status: nr.status,
                },
              };
            }
            return n;
          })
        );
      }

      alert('Workflow run complete!');
    } catch (err) {
      console.error('❌ Run failed', err);
      alert('Workflow run failed');
    } finally {
      setLoading(false);
    }
  };

  const onDragOverWrapper = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const onDropWrapper = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    
    if (!reactFlowWrapper.current) return;

    const dataStr = event.dataTransfer.getData('application/reactflow');
    if (!dataStr) return;

    let parsed: any;
    try {
      parsed = JSON.parse(dataStr);
    } catch (e) {
      return;
    }

    // 2. The Fix: Use screenToFlowPosition directly with clientX/Y.
    // It handles the offset and zoom automatically.
    const position = screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    const id = `agent-${Date.now()}`;
    const newNode: Node = {
      id,
      type: parsed.type || 'agent',
      position,
      data: { label: id, goal: '' },
    };

    setNodes((nds) => nds.concat(newNode));
  };

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      {/* Top Bar */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: 64,
          zIndex: 10,
          background: '#0f172a',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          justifyContent: 'space-between',
        }}
      >
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
            transition: 'background 0.2s',
          }}
        >
          {loading ? 'Running...' : 'Run Workflow'}
        </button>
      </div>

      {/* Layout: Sidebar + Canvas */}
      <div style={{ paddingTop: 64, height: '100vh', display: 'flex' }}>
        <Sidebar />
        
        {/* The wrapper needs the ref for scoping, though screenToFlowPosition handles the heavy math */}
        <div ref={reactFlowWrapper} style={{ flex: 1 }} onDragOver={onDragOverWrapper} onDrop={onDropWrapper}>
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