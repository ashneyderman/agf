import { ThemeToggle } from './components/theme-toggle'

function App() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Hello</h1>
        <p className="text-muted-foreground">
          Welcome to your new Vite + React app with Tailwind CSS and shadcn/ui
        </p>
      </div>
    </div>
  )
}

export default App
