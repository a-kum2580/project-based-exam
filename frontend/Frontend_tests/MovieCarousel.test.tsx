import { render, screen, fireEvent } from '@testing-library/react';
import MovieCarousel from '@/components/MovieCarousel';
import '@testing-library/jest-dom';

// Mock child components to isolate the Carousel's rendering logic
jest.mock('@/components/MovieCard', () => {
  return {
    __esModule: true,
    default: ({ movie }: any) => <div data-testid="movie-card">{movie.title}</div>,
    MovieCardSkeleton: () => <div data-testid="movie-skeleton" />,
  };
});

describe('MovieCarousel Rendering & Interaction', () => {
  const mockMovies = [
    { id: 1, title: 'Inception', vote_average: 8.8 },
    { id: 2, title: 'Interstellar', vote_average: 8.6 },
  ];

  it('renders skeleton loaders dynamically when loading is true', () => {
    render(<MovieCarousel title="Trending" movies={[]} loading={true} />);
    
    expect(screen.getByText('Trending')).toBeInTheDocument();
    
    const skeletons = screen.getAllByTestId('movie-skeleton');
    expect(skeletons.length).toBe(8); // Matches the Array.from({ length: 8 }) in your code
  });

  it('renders movies and interacts with the scroll buttons', () => {
    // @ts-ignore - bypassing full type for brevity in mock
    render(<MovieCarousel title="Top Picks" movies={mockMovies} loading={false} />);
    
    expect(screen.getByText('Top Picks')).toBeInTheDocument();
    expect(screen.getByText('Inception')).toBeInTheDocument();
    expect(screen.getByText('Interstellar')).toBeInTheDocument();

    // Mock HTML element scrollBy method (JSDOM doesn't implement this by default)
    const scrollByMock = jest.fn();
    window.HTMLElement.prototype.scrollBy = scrollByMock;

    // Mock clientWidth since JSDOM defaults layout properties to 0
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
      configurable: true,
      value: 494, // 494 * 0.85 = 419.9 => rounded to 420
    });

    const leftButton = screen.getByLabelText('Scroll left');
    const rightButton = screen.getByLabelText('Scroll right');
    
    fireEvent.click(rightButton);
    expect(scrollByMock).toHaveBeenCalledTimes(1);
    expect(scrollByMock).toHaveBeenCalledWith(expect.objectContaining({ left: 420 }));
    
    // Reset mock for the next interaction to ensure isolation
    scrollByMock.mockClear();

    fireEvent.click(leftButton);
    expect(scrollByMock).toHaveBeenCalledTimes(1);
    expect(scrollByMock).toHaveBeenCalledWith(expect.objectContaining({ left: -420 }));
  });
});
