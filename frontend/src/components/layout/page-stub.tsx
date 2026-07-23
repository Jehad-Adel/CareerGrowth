export function PageStub({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="mt-2 text-muted-foreground">{description}</p>
      <div className="mt-6 rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
        Coming soon — this screen will render live data from your Career Profile.
      </div>
    </div>
  );
}
