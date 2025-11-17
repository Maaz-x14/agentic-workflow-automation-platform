import create from 'zustand'

type State = {
  workflows: any[]
  setWorkflows: (w: any[]) => void
}

export const useStore = create<State>((set) => ({
  workflows: [],
  setWorkflows: (w) => set({ workflows: w }),
}))

export default useStore
