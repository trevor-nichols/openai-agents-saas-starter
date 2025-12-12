// File Path: app/(app)/(workspace)/layout.tsx
// Description: Nested layout for workspace-oriented pages (chat and future multicolumn UIs).
// Sections:
// - WorkspaceLayout component: Provides spacing and ensures full-height content.

interface WorkspaceLayoutProps {
  children: React.ReactNode;
}

export default function WorkspaceLayout({ children }: WorkspaceLayoutProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      {children}
    </div>
  );
}
