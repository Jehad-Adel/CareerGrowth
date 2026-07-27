import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-6 py-24 text-center">
      <p className="font-mono text-sm text-muted-foreground">404</p>
      <h1 className="text-2xl">Nothing grows here</h1>
      <p className="text-sm text-muted-foreground">
        That page does not exist. It may have been moved or never planted.
      </p>
      <div className="flex gap-3">
        <Link href="/dashboard" className={buttonVariants()}>
          Back to your farm
        </Link>
        <Link href="/" className={buttonVariants({ variant: "outline" })}>
          Home
        </Link>
      </div>
    </div>
  );
}
