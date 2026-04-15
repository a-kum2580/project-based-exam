import type { DailyTriviaResponse } from "@/types/trivia";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchDailyTrivia(): Promise<DailyTriviaResponse> {
  const response = await fetch(`${API_BASE}/trivia/daily/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load trivia (${response.status})`);
  }

  return response.json();
}

