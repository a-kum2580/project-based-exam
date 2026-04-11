import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AuthModal from '@/components/AuthModal';
import { useAuth } from '@/lib/AuthContext';
import '@testing-library/jest-dom';

// Mock the AuthContext so we don't make real backend requests
jest.mock('@/lib/AuthContext', () => ({
  useAuth: jest.fn(),
}));

describe('AuthModal Rendering & Interaction', () => {
  const mockLogin = jest.fn();
  const mockRegister = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
    });
  });

  it('does not render when the open prop is false', () => {
    render(<AuthModal open={false} onClose={mockOnClose} />);
    expect(screen.queryByText('Welcome back')).not.toBeInTheDocument();
  });

  it('renders login mode by default and handles submission interactions', async () => {
    render(<AuthModal open={true} onClose={mockOnClose} />);
    
    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    
    // Simulate user typing
    const usernameInput = screen.getByPlaceholderText('Your username');
    const passwordInput = screen.getByPlaceholderText('Your password');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    // Simulate form submission
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  it('toggles to register mode and exposes the email field', async () => {
    render(<AuthModal open={true} onClose={mockOnClose} />);
    
    // Interact with the toggle button
    const signUpToggle = screen.getByText('Sign up');
    fireEvent.click(signUpToggle);

    // Verify the UI state changed
    expect(screen.getByText('Join CineQuest')).toBeInTheDocument();

    // Email input should now be visible and interactive
    const emailInput = screen.getByPlaceholderText('you@example.com');
    expect(emailInput).toBeInTheDocument();

    fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
    
    // The submit button text should have dynamically updated
    const submitButton = screen.getByRole('button', { name: /create account/i });
    expect(submitButton).toBeInTheDocument();
  });
});