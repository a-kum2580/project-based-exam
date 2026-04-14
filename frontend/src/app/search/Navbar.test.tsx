import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import Navbar from "@/components/Navbar";

// Mock Auth Context
jest.mock("@/lib/AuthContext", () => ({
  useAuth: jest.fn(),
}));
import { useAuth } from "@/lib/AuthContext";

// Mock child components to isolate the Navbar test
jest.mock("next/link", () => ({ children, href }: any) => <a href={href}>{children}</a>);
jest.mock("@/components/SearchModal", () => () => <div data-testid="search-modal" />);
jest.mock("@/components/AuthModal", () => () => <div data-testid="auth-modal" />);

describe("Navbar Component", () => {
  it("shows the 'Sign In' button when the user is logged out", () => {
    // Mock the context to simulate a logged-out state
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: jest.fn(),
    });

    render(<Navbar />);
    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("shows the user's username when they are logged in", () => {
    // Mock the context to simulate a logged-in state
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { username: "StudentUser" },
      logout: jest.fn(),
    });

    render(<Navbar />);
    // It should display the username text
    expect(screen.getByText("StudentUser")).toBeInTheDocument();
  });
});
