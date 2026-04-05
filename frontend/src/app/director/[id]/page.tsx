"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Calendar, MapPin, Film, Star, Users } from "lucide-react";
import MovieCard, { MovieCardSkeleton } from "@/components/MovieCard";
import { peopleAPI } from "@/lib/api";
import { formatDate, posterUrl } from "@/lib/utils";

export default function DirectorPage() {
  const params = useParams();
  const personId = Number(params.id);

  const [person, setPerson] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!personId) return;

    async function fetchPerson() {
      setLoading(true);
      try {
        const data = await peopleAPI.enrich(personId);
        setPerson(data);
      } catch (err) {
        console.error(err);
        try {
          const data = await peopleAPI.getDetail(personId);
          setPerson(data);
        } catch {
          console.error("Failed to fetch person");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchPerson();
  }, [personId]);

  if (loading) {
    return (
      <div className="pt-24 pb-20 max-w-6xl mx-auto px-6">
        <div className="flex gap-8">
          <div className="skeleton w-[200px] h-[300px] rounded-2xl" />
          <div className="flex-1 space-y-4">
            <div className="skeleton h-10 w-1/3 rounded-lg" />
            <div className="skeleton h-6 w-1/4 rounded-lg" />
            <div className="skeleton h-32 w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!person) {
    return (
      <div className="pt-24 pb-20 text-center">
        <p className="text-white/40">Person not found.</p>
        <Link href="/search" className="text-gold mt-4 inline-block">
          ← Back to search
        </Link>
      </div>
    );
  }

  const directedMovies = person.directed_movies || [];
  const actedMovies = person.acted_movies || [];

  return (
    <div className="pt-24 pb-20 max-w-6xl mx-auto px-6 md:px-12">
      <Link
        href="/search"
        className="inline-flex items-center gap-2 text-sm text-white/40 hover:text-white/70 mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-8 mb-12">
        {/* Photo */}
        <div className="flex-shrink-0">
          <div className="w-[180px] h-[270px] rounded-2xl overflow-hidden bg-surface-3 shadow-xl">
            {person.profile_url ? (
              <Image
                src={person.profile_url}
                alt={person.name}
                width={180}
                height={270}
                className="w-full h-full object-cover"
                unoptimized
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-4xl text-white/20">
                {person.name?.[0]}
              </div>
            )}
          </div>
        </div>

        {/* Infomation */}
        <div className="flex-1 space-y-4">
          <div>
            <span className="text-xs text-gold font-semibold uppercase tracking-wider">
              {person.known_for_department || "Filmmaker"}
            </span>
            <h1 className="text-4xl font-bold font-display mt-1">{person.name}</h1>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-white/50">
            {person.birthday && (
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {formatDate(person.birthday)}
              </span>
            )}
            {person.place_of_birth && (
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {person.place_of_birth}
              </span>
            )}
          </div>

          {person.biography && (
            <p className="text-white/60 leading-relaxed max-w-2xl line-clamp-6">
              {person.biography}
            </p>
          )}

          <div className="flex gap-6 pt-2">
            {directedMovies.length > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Film className="w-4 h-4 text-gold" />
                <span>{directedMovies.length} films directed</span>
              </div>
            )}
            {actedMovies.length > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Star className="w-4 h-4 text-yellow-400" />
                <span>{actedMovies.length} acting credits</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Directed movies */}
      {directedMovies.length > 0 && (
        <section className="mb-12">
          <h2 className="text-xl font-bold font-display flex items-center gap-2 mb-6">
            <Film className="w-5 h-5 text-gold" />
            Directed
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-5">
            {directedMovies.map((movie: any) => (
              <MovieCard key={movie.id || movie.tmdb_id} movie={movie} />
            ))}
          </div>
        </section>
      )}

      {/* Acted in */}
      {actedMovies.length > 0 && (
        <section>
          <h2 className="text-xl font-bold font-display flex items-center gap-2 mb-6">
            <Users className="w-5 h-5 text-gold" />
            Acted In
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-5">
            {actedMovies.map((movie: any) => (
              <MovieCard key={movie.id || movie.tmdb_id} movie={movie} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

