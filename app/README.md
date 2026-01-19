# Frontend App

A React application built with Vite, Tailwind CSS, and shadcn/ui components.

## Features

- ⚡️ Vite for fast development and building
- ⚛️ React 18 with TypeScript
- 🎨 Tailwind CSS for styling
- 🧩 shadcn/ui component library
- 🌓 Dark/Light theme support with theme toggle
- 📦 Path aliases configured (@/*)

## Getting Started

### Development

```bash
npm install
npm run dev
```

The app will be available at http://localhost:5173

### Build

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview

```bash
npm run preview
```

## Project Structure

```
app/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── theme-provider.tsx
│   │   └── theme-toggle.tsx
│   ├── lib/
│   │   └── utils.ts      # Utility functions
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # App entry point
│   └── index.css         # Global styles with Tailwind
├── public/               # Static assets
└── components.json       # shadcn/ui configuration
```

## Theme Management

The app includes a theme toggle button in the top-right corner that cycles through:
- Light mode
- Dark mode
- System preference

Theme preference is persisted in localStorage.

## Adding shadcn/ui Components

To add new shadcn/ui components:

```bash
npx shadcn@latest add [component-name]
```

For example:
```bash
npx shadcn@latest add card
npx shadcn@latest add input
```
