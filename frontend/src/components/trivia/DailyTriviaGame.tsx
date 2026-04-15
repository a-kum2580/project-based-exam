"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, CircleHelp, RefreshCw, XCircle } from "lucide-react";
import type { TriviaQuestion } from "@/types/trivia";

interface DailyTriviaGameProps {
  triviaDate: string;
  questions: TriviaQuestion[];
}

export default function DailyTriviaGame({ triviaDate, questions }: DailyTriviaGameProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);

  const activeQuestion = questions[activeIndex];
  const selectedIndex = activeQuestion ? answers[activeQuestion.id] : undefined;

  const score = useMemo(() => {
    return questions.reduce((total, question) => {
      const selected = answers[question.id];
      return selected === question.correct_index ? total + 1 : total;
    }, 0);
  }, [answers, questions]);

  function handleSelect(optionIndex: number) {
    if (submitted || !activeQuestion) {
      return;
    }
    setAnswers((prev) => ({ ...prev, [activeQuestion.id]: optionIndex }));
  }

  function handleNext() {
    if (activeIndex < questions.length - 1) {
      setActiveIndex((prev) => prev + 1);
      return;
    }
    setSubmitted(true);
  }

  function handleReset() {
    setActiveIndex(0);
    setAnswers({});
    setSubmitted(false);
  }

  if (!questions.length) {
    return (
      <div className="glass-card rounded-2xl p-8 text-center">
        <CircleHelp className="w-10 h-10 text-gold/40 mx-auto mb-3" />
        <p className="text-white/50">Not enough local movie data to generate trivia yet.</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-6 md:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-gold/80">Daily Trivia</p>
          <p className="text-sm text-white/40 mt-1">{triviaDate}</p>
        </div>
        <p className="text-sm text-white/40">
          Question {Math.min(activeIndex + 1, questions.length)} of {questions.length}
        </p>
      </div>

      {submitted ? (
        <div className="text-center py-4">
          <CheckCircle2 className="w-14 h-14 text-emerald-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold font-display mb-2">Challenge Complete</h2>
          <p className="text-white/50 mb-6">
            You scored <span className="text-gold font-semibold">{score}</span> / {questions.length}
          </p>
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Play Again
          </button>
        </div>
      ) : (
        <>
          <h2 className="text-xl md:text-2xl font-bold font-display mb-5 leading-snug">
            {activeQuestion.prompt}
          </h2>

          <div className="space-y-3">
            {activeQuestion.options.map((option, optionIndex) => {
              const isSelected = selectedIndex === optionIndex;
              return (
                <button
                  key={`${activeQuestion.id}-${optionIndex}`}
                  type="button"
                  onClick={() => handleSelect(optionIndex)}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-colors ${
                    isSelected
                      ? "border-gold/60 bg-gold/10 text-white"
                      : "border-white/10 bg-white/[0.03] text-white/75 hover:bg-white/[0.06]"
                  }`}
                >
                  {option}
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex items-center justify-between">
            <p className="text-xs text-white/40">
              {selectedIndex === undefined
                ? "Choose one answer to continue"
                : "Answer locked. Move to the next question."}
            </p>
            <button
              type="button"
              onClick={handleNext}
              disabled={selectedIndex === undefined}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 text-sm font-semibold disabled:opacity-50"
            >
              {activeIndex === questions.length - 1 ? "Submit" : "Next"}
            </button>
          </div>
        </>
      )}

      {submitted && (
        <div className="mt-8 border-t border-white/10 pt-6 space-y-3">
          {questions.map((question) => {
            const chosen = answers[question.id];
            const correct = question.correct_index;
            const isCorrect = chosen === correct;
            return (
              <div
                key={question.id}
                className="rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3"
              >
                <div className="flex items-start gap-2">
                  {isCorrect ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 mt-0.5" />
                  )}
                  <div>
                    <p className="text-sm text-white/80">{question.prompt}</p>
                    <p className="text-xs text-white/45 mt-1">
                      Correct: {question.options[correct]}
                      {chosen !== undefined ? ` | Your answer: ${question.options[chosen]}` : ""}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

