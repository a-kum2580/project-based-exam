export interface MovieCompact {
  id: number;
  tmdb_id: number;
  title: string;
  overview?: string;
  release_date?: string;
  year?: number;
  vote_average: number;
  vote_count: number;
  popularity: number;
  poster_url?: string;
  poster_url_small?: string;
  genres: Genre[];
  runtime?: number;
}

export interface MovieDetail {
  id: number;
  tmdb_id: number;
  imdb_id?: string;
  title: string;
  original_title?: string;
  overview?: string;
  tagline?: string;
  release_date?: string;
  year?: number;
  runtime?: number;
  vote_average: number;
  vote_count: number;
  popularity: number;
  poster_url?: string;
  backdrop_url?: string;
  trailer_url?: string;
  trailer_embed_url?: string;
  trailer_key?: string;
  budget: number;
  revenue: number;
  status?: string;
  homepage?: string;
  genres: Genre[];
  directors: Person[];
  cast: MovieCast[];
  watch_providers: WatchProvider[];
  wikipedia_url?: string;
  wikipedia_summary?: string;
}

export interface Genre {
  id: number;
  tmdb_id: number;
  name: string;
  slug: string;
  movie_count: number;
}

export interface Person {
  id: number;
  tmdb_id: number;
  name: string;
  profile_url?: string;
  biography?: string;
  birthday?: string;
  place_of_birth?: string;
  known_for_department?: string;
  directed_movies?: MovieCompact[];
  acted_movies?: MovieCompact[];
}

export interface MovieCast {
  person: Person;
  character: string;
  order: number;
}

export interface WatchProvider {
  provider_name: string;
  provider_type: string;
  logo_url?: string;
  link: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  avatar_url?: string;
  favorite_genres: number[];
  country_code: string;
  date_joined: string;
}

export interface GenrePreference {
  genre_tmdb_id: number;
  genre_name: string;
  weight: number;
  interaction_count: number;
  updated_at: string;
}

export interface WatchlistItem {
  id: number;
  movie_tmdb_id: number;
  movie_title: string;
  poster_path?: string;
  poster_url?: string;
  added_at: string;
  watched: boolean;
  watched_at?: string;
}
