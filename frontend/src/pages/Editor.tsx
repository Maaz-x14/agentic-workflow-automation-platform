import React from 'react'
import FlowEditor from '../workflow-editor/FlowEditor'

export default function Editor() {
  return (
    <div>
      <h2>Workflow Editor</h2>
      <div className="editor-canvas">
        <FlowEditor />
      </div>
    </div>
  )
}
