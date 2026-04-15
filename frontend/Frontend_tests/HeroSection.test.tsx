import { render, screen } from '@testing-library/react';
import HeroSection from '@/components/HeroSection';
import '@testing-library/jest-dom';

// Mock Next.js Image and Link components
jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ fill, unoptimized, priority, ...props }: any) => <img {...props} />,
}));

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: any) => <a href={href}>{children}</a>,
}));

describe('HeroSection', () => {
  it('renders safe fallback UI when movies is undefined or null', () => {
    // @ts-ignore - explicitly simulating runtime type mismatch
    render(<HeroSection movies={undefined} />);
    
    // Should render the fallback title screen instead of crashing
    expect(screen.getByText('Quest')).toBeInTheDocument(); 
    expect(screen.getByText('Your cinematic discovery engine')).toBeInTheDocument();
  });

  it('renders valid movies correctly', () => {
    const mockMovies = [
      { id: 1, title: 'Inception', vote_average: 8.8, overview: 'A dream within a dream.', genres: [] }
    ];
    
    // @ts-ignore
    render(<HeroSection movies={mockMovies} />);
    
    expect(screen.getByText('Inception')).toBeInTheDocument();
    expect(screen.getByText('A dream within a dream.')).toBeInTheDocument();
  });
});