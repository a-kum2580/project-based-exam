import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ComparePage from '@/app/compare/page';
import { moviesAPI } from '@/lib/api';
import '@testing-library/jest-dom';

// Mock API and Next elements
jest.mock('@/lib/api', () => ({
  moviesAPI: {
    search: jest.fn(),
    getDetail: jest.fn(),
  }
}));

jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => <img {...props} priority={undefined} />,
}));

describe('ComparePage Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('debounces search inputs and calls the API', async () => {
    (moviesAPI.search as jest.Mock).mockResolvedValue({
      results: [{ id: 101, title: 'The Matrix', year: '1999' }]
    });

    render(<ComparePage />);
    
    const inputA = screen.getByPlaceholderText('Search movie A...');
    fireEvent.change(inputA, { target: { value: 'Matrix' } });
    
    // Wait for the 500ms debounce to fire the API call
    await waitFor(() => {
      expect(moviesAPI.search).toHaveBeenCalledWith('Matrix');
    }, { timeout: 1000 });

    expect(await screen.findByText('The Matrix')).toBeInTheDocument();
  });
});