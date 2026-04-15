import { render, screen } from '@testing-library/react';
import Navbar from '@/components/Navbar';
import { useAuth } from '@/lib/AuthContext';
import '@testing-library/jest-dom';

// Mock hooks and child components
jest.mock('@/lib/AuthContext', () => ({
  useAuth: jest.fn(),
}));
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: any) => <a href={href}>{children}</a>,
}));
jest.mock('@/components/SearchModal', () => () => <div data-testid="search-modal" />);
jest.mock('@/components/AuthModal', () => () => <div data-testid="auth-modal" />);

describe('Navbar Authentication States', () => {
  it('shows Sign In button for unauthenticated users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: jest.fn()
    });
    
    render(<Navbar />);
    
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });

  it('shows User avatar and Dashboard for authenticated users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { username: 'JohnDoe' },
      isAuthenticated: true,
      logout: jest.fn()
    });
    
    render(<Navbar />);
    
    // Verifies the user's username is visible
    expect(screen.getByText('JohnDoe')).toBeInTheDocument();
    // Dashboard links should be rendered in the nav
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
  });
});