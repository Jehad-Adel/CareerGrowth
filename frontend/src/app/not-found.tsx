import Link from "next/link";
import { connection } from "next/server";

import { buttonVariants } from "@/components/ui/button";

// Dynamic for the same reason as `/` — a prerendered 404 carries scripts with
// no nonce, which the CSP then blocks.
export default async function NotFound() {
  await connection();

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
