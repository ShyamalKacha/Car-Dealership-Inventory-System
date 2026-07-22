import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ui/ThemeToggle";
import { Button } from "./ui/Button";

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] flex flex-col">
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-bg-primary)]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="text-xl font-bold tracking-tight">
            CarDealership
          </Link>

          <nav className="flex items-center gap-4">
            <ThemeToggle />

            {isAuthenticated ? (
              <>
                <span className="text-sm text-[var(--color-text-secondary)]">
                  {user?.username}
                  {user?.role === "admin" && (
                    <span className="ml-1.5 rounded-full bg-[var(--color-accent)] px-2 py-0.5 text-xs text-white">
                      admin
                    </span>
                  )}
                </span>
                {user?.role === "admin" && (
                  <Link to="/admin">
                    <Button variant="secondary" type="button">
                      Admin
                    </Button>
                  </Link>
                )}
                <Button variant="ghost" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <Link to="/login">
                <Button variant="primary" type="button">
                  Sign In
                </Button>
              </Link>
            )}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>
    </div>
  );
}
