import { render, screen } from '@testing-library/react';
import MovieCard from '@/components/MovieCard';
import '@testing-library/jest-dom';

// Mock Next.js Image and Link components
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => <img {...props} priority={undefined} />,
}));

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: any) => <a href={href}>{children}</a>,
}));

describe('MovieCard', () => {
  const mockMovie = {
    id: 101,
    tmdb_id: 101,
    title: 'The Dark Knight',
    poster_path: '/dark-knight-poster.jpg',
    vote_average: 9.0,
    year: '2008',
    runtime: 152, // 2h 32m
    overview: 'When the menace known as the Joker wreaks havoc and chaos...',
    genres: [],
  };

  it('renders the movie title and year correctly', () => {
    // @ts-ignore - bypassing full MovieCompact type strictness for mock
    render(<MovieCard movie={mockMovie} />);
    
    expect(screen.getByText('The Dark Knight')).toBeInTheDocument();
    expect(screen.getByText('2008')).toBeInTheDocument();
  });

  it('displays the rating badge when vote_average > 0', () => {
    // @ts-ignore
    render(<MovieCard movie={mockMovie} />);
    expect(screen.getByText('9.0')).toBeInTheDocument();
  });

  it('displays the overview only when showOverview prop is true', () => {
    // @ts-ignore
    const { rerender } = render(<MovieCard movie={mockMovie} showOverview={false} />);
    expect(screen.queryByText(/When the menace known as the Joker/)).not.toBeInTheDocument();
    
    // @ts-ignore
    rerender(<MovieCard movie={mockMovie} showOverview={true} />);
    expect(screen.getByText(/When the menace known as the Joker/)).toBeInTheDocument();
  });
});
