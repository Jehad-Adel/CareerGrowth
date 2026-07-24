import { ClosingCta } from "@/components/landing/closing-cta";
import { Connected } from "@/components/landing/connected";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { LandingNav } from "@/components/landing/landing-nav";
import { MotionProvider } from "@/components/landing/motion-provider";
import { SiteFooter } from "@/components/landing/site-footer";
import { Stats } from "@/components/landing/stats";
import { Steps } from "@/components/landing/steps";

export default function Home() {
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
