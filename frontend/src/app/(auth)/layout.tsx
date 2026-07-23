import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-xl">
            🌱
          </span>
          <span className="font-heading text-lg font-semibold">CareerFarm</span>
        </Link>
        {children}
      </div>
    </div>
  );
}
