import { describe, it, expect, beforeEach } from 'vitest'
import { useLabStore } from '../lab-store'

describe('useLabStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useLabStore.setState({
      conversations: [],
      activeConversationId: null,
      chatMessages: [],
      sidebarCollapsed: false,
      activeTool: 'chat',
      pendingPrompt: null,
      voiceModeActive: false,
    })
  })

  it('initial state has empty conversations', () => {
    const state = useLabStore.getState()
    expect(state.conversations).toHaveLength(0)
    expect(state.activeConversationId).toBeNull()
  })

  it('startNewConversation clears active conversation and messages', () => {
    useLabStore.setState({
      activeConversationId: 'some-id',
      chatMessages: [{ id: '1', role: 'user', content: 'hi', timestamp: new Date().toISOString() }],
    })
    useLabStore.getState().startNewConversation()
    const state = useLabStore.getState()
    expect(state.activeConversationId).toBeNull()
    expect(state.chatMessages).toHaveLength(0)
  })

  it('addConversation prepends and sets active', () => {
    const conv = {
      id: 'conv-1',
      title: 'Test conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    useLabStore.getState().addConversation(conv)
    const state = useLabStore.getState()
    expect(state.conversations).toHaveLength(1)
    expect(state.conversations[0].id).toBe('conv-1')
    expect(state.activeConversationId).toBe('conv-1')
  })

  it('addMessage adds a chat message', () => {
    useLabStore.getState().addMessage('user', 'Hello')
    const state = useLabStore.getState()
    expect(state.chatMessages).toHaveLength(1)
    expect(state.chatMessages[0].role).toBe('user')
    expect(state.chatMessages[0].content).toBe('Hello')
    expect(state.chatMessages[0].id).toBeDefined()
    expect(state.chatMessages[0].timestamp).toBeDefined()
  })

  it('addMessage appends messages in order', () => {
    const store = useLabStore.getState()
    store.addMessage('user', 'First')
    store.addMessage('assistant', 'Second')
    const state = useLabStore.getState()
    expect(state.chatMessages).toHaveLength(2)
    expect(state.chatMessages[0].content).toBe('First')
    expect(state.chatMessages[1].content).toBe('Second')
  })

  it('toggleSidebar toggles collapsed state', () => {
    expect(useLabStore.getState().sidebarCollapsed).toBe(false)
    useLabStore.getState().toggleSidebar()
    expect(useLabStore.getState().sidebarCollapsed).toBe(true)
    useLabStore.getState().toggleSidebar()
    expect(useLabStore.getState().sidebarCollapsed).toBe(false)
  })

  it('setPendingPrompt sets and clears prompt', () => {
    useLabStore.getState().setPendingPrompt('Run analysis')
    expect(useLabStore.getState().pendingPrompt).toBe('Run analysis')
    useLabStore.getState().setPendingPrompt(null)
    expect(useLabStore.getState().pendingPrompt).toBeNull()
  })

  it('clearMessages empties chat messages', () => {
    useLabStore.getState().addMessage('user', 'Hello')
    useLabStore.getState().addMessage('assistant', 'Hi there')
    expect(useLabStore.getState().chatMessages).toHaveLength(2)
    useLabStore.getState().clearMessages()
    expect(useLabStore.getState().chatMessages).toHaveLength(0)
  })
})
