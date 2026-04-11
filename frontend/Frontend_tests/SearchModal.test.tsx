import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchModal from '@/components/SearchModal';
import { moviesAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import '@testing-library/jest-dom';

// Mock Next.js routing, image, and API
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  moviesAPI: {
    search: jest.fn(),
  },
}));

jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ fill, unoptimized, priority, ...props }: any) => <img {...props} />,
}));

describe('SearchModal', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  });

  it('does not render when open is false', () => {
    render(<SearchModal open={false} onClose={jest.fn()} />);
    expect(screen.queryByPlaceholderText(/Search movies/i)).not.toBeInTheDocument();
  });

  it('renders, accepts input, and calls search API', async () => {
    (moviesAPI.search as jest.Mock).mockResolvedValue({
      results: [{ id: 1, title: 'Inception', year: '2010', vote_average: 8.8 }]
    });

    render(<SearchModal open={true} onClose={jest.fn()} />);

    const input = screen.getByPlaceholderText(/Search movies/i);
    expect(input).toBeInTheDocument();

    fireEvent.change(input, { target: { value: 'Incep' } });

    await waitFor(() => {
      expect(moviesAPI.search).toHaveBeenCalledWith('Incep');
    });

    expect(await screen.findByText('Inception')).toBeInTheDocument();
  });
});