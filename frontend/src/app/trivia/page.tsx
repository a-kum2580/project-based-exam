"use client";

import { useEffect, useState } from "react";
import { Clapperboard, Loader2 } from "lucide-react";
import DailyTriviaGame from "@/components/trivia/DailyTriviaGame";
import { fetchDailyTrivia } from "@/lib/trivia-api";
import type { DailyTriviaResponse } from "@/types/trivia";

export default function DailyTriviaPage() {
  const [data, setData] = useState<DailyTriviaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchDailyTrivia();
        if (mounted) {
          setData(response);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load daily trivia");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1000px] mx-auto">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/15 mb-5">
          <Clapperboard className="w-3.5 h-3.5 text-gold" />
          <span className="text-[11px] font-semibold uppercase tracking-widest text-gold">
            Human Element
          </span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold font-display mb-3">
          Daily <span className="text-gold italic">Cinema Trivia</span>
        </h1>
        <p className="text-white/35 max-w-xl mx-auto">
          Five fresh questions generated from your local movie catalog every day.
        </p>
      </div>

      {loading && (
        <div className="glass-card rounded-2xl p-10 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-gold/60" />
        </div>
      )}

      {!loading && error && (
        <div className="glass-card rounded-2xl p-8 text-center">
          <p className="text-rose-300">{error}</p>
        </div>
      )}

      {!loading && !error && data && (
        <DailyTriviaGame triviaDate={data.date} questions={data.questions} />
      )}
    </div>
  );
}

