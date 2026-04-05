"use client";

import Link from "next/link";
import {
  Sparkles, Heart, Zap, Brain, Smile, Ghost,
  Mountain, ArrowRight,
} from "lucide-react";

const MOODS_PREVIEW = [
  { slug: "cozy-night", label: "Cozy Night", icon: Heart, color: "from-pink-500/20 to-rose-600/20", iconColor: "text-pink-400" },
  { slug: "adrenaline", label: "Adrenaline", icon: Zap, color: "from-red-500/20 to-orange-600/20", iconColor: "text-red-400" },
  { slug: "mind-bender", label: "Mind Bender", icon: Brain, color: "from-violet-500/20 to-purple-600/20", iconColor: "text-violet-400" },
  { slug: "feel-good", label: "Feel Good", icon: Smile, color: "from-yellow-500/20 to-amber-500/20", iconColor: "text-yellow-400" },
  { slug: "edge-of-seat", label: "Suspense", icon: Ghost, color: "from-slate-500/20 to-neutral-600/20", iconColor: "text-slate-400" },
  { slug: "epic-adventure", label: "Adventure", icon: Mountain, color: "from-emerald-500/20 to-teal-600/20", iconColor: "text-emerald-400" },
];

export default function MoodTeaser() {
  return (
    <section className="px-6 md:px-10 lg:px-20">
      <div className="glass-card rounded-2xl p-8 md:p-10 relative overflow-hidden">
        {/* Decorative */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/20 to-transparent" />
        <div className="absolute -top-20 -right-20 w-80 h-80 bg-gradient-to-bl from-gold/[0.04] to-transparent rounded-full pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-center gap-8">
          {/* Left */}
          <div className="flex-1 space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/15">
              <Sparkles className="w-3.5 h-3.5 text-gold" />
              <span className="text-[11px] font-semibold uppercase tracking-widest text-gold">
                Mood Picker
              </span>
            </div>

            <h2 className="text-3xl md:text-4xl font-bold font-display leading-tight">
              Not sure what<br />
              <span className="text-gold italic">to watch?</span>
            </h2>

            <p className="text-white/35 max-w-md">
              Pick your current mood and get curated movie picks that match exactly how you&apos;re feeling.
            </p>

            <Link
              href="/mood"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold text-sm hover:shadow-lg hover:shadow-gold/20 transition-all duration-300 hover:scale-[1.03] group"
            >
              Pick Your Mood
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {/*  Mood pills */}
          <div className="grid grid-cols-3 gap-2.5 lg:gap-3">
            {MOODS_PREVIEW.map((mood) => {
              const Icon = mood.icon;
              return (
                <Link
                  key={mood.slug}
                  href={`/mood?mood=${mood.slug}`}
                  className="genre-card glass-card group rounded-xl p-4 text-center relative overflow-hidden"
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${mood.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                  <div className="relative z-10">
                    <Icon className={`w-5 h-5 mx-auto mb-1.5 text-white/25 group-hover:${mood.iconColor} transition-colors`} />
                    <p className="text-[11px] font-semibold text-white/50 group-hover:text-white/80 transition-colors">{mood.label}</p>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
