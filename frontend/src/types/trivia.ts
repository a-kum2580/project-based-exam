export interface TriviaQuestion {
  id: number;
  kind: "release_year" | "cast_member";
  prompt: string;
  options: string[];
  correct_index: number;
  movie_tmdb_id: number;
  movie_title: string;
}

export interface DailyTriviaResponse {
  date: string;
  questions: TriviaQuestion[];
}

