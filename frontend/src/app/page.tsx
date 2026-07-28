import { connection } from "next/server";

import { ClosingCta } from "@/components/landing/closing-cta";
import { Connected } from "@/components/landing/connected";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { LandingNav } from "@/components/landing/landing-nav";
import { MotionProvider } from "@/components/landing/motion-provider";
import { SiteFooter } from "@/components/landing/site-footer";
import { Stats } from "@/components/landing/stats";
import { Steps } from "@/components/landing/steps";

// Prerendering this page would freeze its <script> tags at build time, where
// there is no request and therefore no CSP nonce — the browser then blocks
// every one of them and the landing page renders but never hydrates. Waiting
// on the connection opts it into per-request rendering so Next can stamp the
// nonce in. The same applies to every route that ships HTML; `/` and
// `/signup` were the only two still static.
export default async function Home() {
  await connection();

  return (
    <div className="min-h-screen">
      <LandingNav />
      <MotionProvider>
        <main>
          <Hero />
          <Steps />
          <Features />
          <Connected />
          <Stats />
          <ClosingCta />
        </main>
      </MotionProvider>
      <SiteFooter />
    </div>
  );
}
