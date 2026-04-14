import { Component } from 'react'
import type { ReactNode, ErrorInfo } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Patch DOM methods to prevent "removeChild" errors caused by browser extensions
// (translators, ad blockers, etc.) that modify the DOM outside React's control.
if (typeof Node !== 'undefined') {
  const origRemoveChild = Node.prototype.removeChild as any
  Node.prototype.removeChild = function <T extends Node>(child: T): T {
    if (child.parentNode !== this) {
      console.warn('[DOM patch] removeChild: child not found, skipping')
      return child
    }
    return origRemoveChild.call(this, child)
  }

  const origInsertBefore = Node.prototype.insertBefore as any
  Node.prototype.insertBefore = function <T extends Node>(newNode: T, refNode: Node | null): T {
    if (refNode && refNode.parentNode !== this) {
      console.warn('[DOM patch] insertBefore: refNode not found, appending')
      return origInsertBefore.call(this, newNode, null)
    }
    return origInsertBefore.call(this, newNode, refNode)
  }
}

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('React Error:', error, info)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, fontFamily: 'monospace' }}>
          <h1 style={{ color: 'red' }}>页面渲染出错</h1>
          <pre style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}>
            {this.state.error?.message}
            {'\n\n'}
            {this.state.error?.stack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
)
