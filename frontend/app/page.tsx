"use client";

import { useRef } from "react";
import Hero from "./components/Hero";
import HeroProductVisual, { HeroProductVisualHandle } from "./components/HeroProductVisual";
import PlatformSignalStrip from "./components/PlatformSignalStrip";
import WhyVidSnap from "./components/WhyVidSnap";
import HowItWorks from "./components/HowItWorks";
import StoryFirstDemo from "./components/StoryFirstDemo";
import TemplateGallery from "./components/TemplateGallery";
import CreatorProof from "./components/CreatorProof";
import FinalCTA from "./components/FinalCTA";

export default function HomePage() {
  const visualRef = useRef<HeroProductVisualHandle | null>(null);

  const handleWatchDemo = () => {
    visualRef.current?.scrollIntoView();
    visualRef.current?.playVideo();
  };

  return (
    <div className="flex flex-col items-center w-full overflow-x-clip">
      {/* 1. Hero Section with 2-Column Responsive Layout */}
      <section className="relative w-full pt-10 pb-16 sm:pt-16 sm:pb-24 lg:pt-20 lg:pb-28 radial-glow-hero">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            <div className="lg:col-span-7">
              <Hero onWatchDemo={handleWatchDemo} />
            </div>
            <div className="lg:col-span-5 flex justify-center lg:justify-end">
              <HeroProductVisual ref={visualRef} />
            </div>
          </div>
        </div>
      </section>

      {/* 2. Platform Signal Strip */}
      <PlatformSignalStrip />

      {/* 3. Why VidSnap */}
      <WhyVidSnap />

      {/* 4. How It Works */}
      <HowItWorks />

      {/* 5. Story-First Editor Demonstration */}
      <StoryFirstDemo />

      {/* 6. Popular Templates Gallery */}
      <TemplateGallery />

      {/* 7. Creator Workflow Proof */}
      <CreatorProof />

      {/* 8. Final CTA Banner */}
      <FinalCTA />
    </div>
  );
}
