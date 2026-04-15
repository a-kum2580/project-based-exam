import { render, screen, waitFor } from '@testing-library/react';
import HomePage from '@/app/page';
import { moviesAPI } from '@/lib/api';
import '@testing-library/jest-dom';

// Mock external data and heavy components
jest.mock('@/lib/api', () => ({
  moviesAPI: {
    trending: jest.fn(),
    nowPlaying: jest.fn(),
    topRated: jest.fn(),
  }
}));

jest.mock('@/components/HeroSection', () => () => <div data-testid="hero-mock" />);
jest.mock('@/components/MovieCarousel', () => ({ title }: any) => <div data-testid="carousel-mock">{title}</div>);
jest.mock('@/components/GenreGrid', () => () => <div data-testid="genre-grid-mock" />);
jest.mock('@/components/PersonalizedSection', () => () => <div data-testid="personalized-mock" />);
jest.mock('@/components/MoodTeaser', () => () => <div data-testid="mood-mock" />);

describe('HomePage Data Fetching', () => {
  it('fetches initial data and renders expected sections', async () => {
    (moviesAPI.trending as jest.Mock).mockResolvedValue({ results: [] });
    (moviesAPI.nowPlaying as jest.Mock).mockResolvedValue({ results: [] });
    (moviesAPI.topRated as jest.Mock).mockResolvedValue({ results: [] });

    render(<HomePage />);

    await waitFor(() => {
      expect(moviesAPI.trending).toHaveBeenCalled();
      expect(moviesAPI.nowPlaying).toHaveBeenCalled();
      expect(moviesAPI.topRated).toHaveBeenCalled();
    });

    expect(screen.getByTestId('hero-mock')).toBeInTheDocument();
    expect(screen.getByText('Trending This Week')).toBeInTheDocument();
  });
});