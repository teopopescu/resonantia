import { describe, it, expect, beforeEach } from 'vitest'
import { useLabStore } from '../lab-store'

describe('useLabStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useLabStore.setState({
      tasks: [
        {
          id: 'default-1',
          title: 'Plate mapping for experiment A',
          createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
          status: 'active',
        },
        {
          id: 'default-2',
          title: 'Microscopy image analysis',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          status: 'active',
        },
        {
          id: 'default-3',
          title: 'Sample inventory check',
          createdAt: new Date(Date.now() - 3600000 * 5).toISOString(),
          status: 'completed',
        },
      ],
      activeTaskId: null,
      chatMessages: [],
      sidebarCollapsed: false,
      activeTool: 'chat',
      activeTab: 'tasks',
      pendingPrompt: null,
    })
  })

  it('initial state has default tasks', () => {
    const state = useLabStore.getState()
    expect(state.tasks).toHaveLength(3)
    expect(state.tasks[0].title).toBe('Plate mapping for experiment A')
    expect(state.tasks[1].title).toBe('Microscopy image analysis')
    expect(state.tasks[2].title).toBe('Sample inventory check')
  })

  it('addTask adds a task with correct fields', () => {
    useLabStore.getState().addTask('New experiment task')
    const state = useLabStore.getState()
    expect(state.tasks).toHaveLength(4)
    // New task is prepended
    const newTask = state.tasks[0]
    expect(newTask.title).toBe('New experiment task')
    expect(newTask.status).toBe('active')
    expect(newTask.id).toBeDefined()
    expect(newTask.createdAt).toBeDefined()
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
})
