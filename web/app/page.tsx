export default function Home() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <main className="flex flex-col items-center gap-6 p-8">
        <h1 className="text-3xl font-bold text-text-primary">
          ProgramingEducation
        </h1>
        <p className="text-text-secondary">
          AI-powered C++ programming education platform
        </p>
        <div className="flex gap-3">
          <button className="h-8 px-4 rounded-md bg-btn-primary-bg text-white text-sm font-medium hover:bg-btn-primary-hover transition-colors">
            Primary
          </button>
          <button className="h-8 px-4 rounded-md bg-btn-default-bg border border-btn-default-border text-text-primary text-sm font-medium hover:bg-bg-subtle transition-colors">
            Default
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="p-4 rounded-md bg-bg-default border border-border-default">
            <p className="text-sm text-text-secondary">Card on bg-default</p>
          </div>
          <div className="p-4 rounded-md bg-bg-subtle border border-border-muted">
            <p className="text-sm text-text-muted">Card on bg-subtle</p>
          </div>
        </div>
        <code className="mt-2 px-3 py-2 rounded-md bg-bg-inset border border-border-default font-mono text-sm text-accent-green">
          std::cout &lt;&lt; &quot;Hello, World!&quot; &lt;&lt; std::endl;
        </code>
      </main>
    </div>
  );
}
