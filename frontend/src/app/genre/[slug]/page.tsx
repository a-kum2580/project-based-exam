"use client";

import { useState, useEffect, Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import MovieCard, { MovieCardSkeleton } from "@/components/MovieCard";
import { genresAPI } from "@/lib/api";
import type { MovieCompact } from "@/types/movie";

function GenreContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const genreId = searchParams.get("id");

  const [movies, setMovies] = useState<MovieCompact[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const genreName = slug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  useEffect(() => {
    async function fetchMovies() {
      setLoading(true);
      try {
        const data = await genresAPI.getMovies(slug, page);
        setMovies(data.results || []);
        setTotalPages(data.total_pages || 1);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchMovies();
  }, [slug, page]);

  return (
    <div className="pt-24 pb-20 px-6 md:px-12 lg:px-20 max-w-[1400px] mx-auto">
      <Link
        href="/genre"
        className="inline-flex items-center gap-2 text-sm text-white/40 hover:text-white/70 mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> All Genres
      </Link>

      <h1 className="text-3xl font-bold font-display mb-8">{genreName} Movies</h1>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          {Array.from({ length: 18 }).map((_, i) => (
            <MovieCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {movies.map((movie) => (
              <MovieCard key={movie.id || movie.tmdb_id} movie={movie} showOverview />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-12">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-5 py-2.5 rounded-xl glass-card text-sm font-medium disabled:opacity-20 hover:border-gold/15 transition-all"
              >
                Previous
              </button>
              <span className="text-sm text-white/30 font-mono tabular-nums px-4">
                {page} / {Math.min(totalPages, 500)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages}
                className="px-5 py-2.5 rounded-xl glass-card text-sm font-medium disabled:opacity-20 hover:border-gold/15 transition-all"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function GenreDetailPage() {
  return (
    <Suspense fallback={<div className="pt-32 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-gold/40" /></div>}>
      <GenreContent />
    </Suspense>
  );
}
