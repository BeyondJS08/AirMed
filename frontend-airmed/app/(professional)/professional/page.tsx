export default function ProfessionalOverviewPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Welcome to your professional dashboard
        </p>
      </div>
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <p>Overview and stats coming in Layer 6C.</p>
      </div>
    </div>
  )
}
