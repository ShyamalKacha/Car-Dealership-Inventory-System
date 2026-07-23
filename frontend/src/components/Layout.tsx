import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ui/ThemeToggle";
import { Button } from "./ui/Button";

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] flex flex-col transition-colors duration-300">
      <header className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-bg-card)]/85 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to={isAuthenticated && user?.role === "admin" ? "/admin" : "/"} className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent)] text-white text-sm font-bold tracking-tight">
              CD
            </div>
            <span className="text-lg font-semibold tracking-tight text-[var(--color-text-primary)]">
              CarDealership
            </span>
          </Link>

          <nav className="flex items-center gap-2">
            <ThemeToggle />

            {isAuthenticated ? (
              <>
                {user?.role === "admin" && (
                  <Link
                    to="/admin"
                    className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive("/admin")
                        ? "bg-[var(--color-accent-light)] text-[var(--color-accent)]"
                        : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]"
                    }`}
                  >
                    Admin
                  </Link>
                )}

                <div className="flex items-center gap-2 pl-2 border-l border-[var(--color-border)]">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-accent-light)] text-[var(--color-accent)] text-xs font-semibold">
                    {user?.username?.[0]?.toUpperCase()}
                  </div>
                  <span className="hidden sm:inline text-sm text-[var(--color-text-secondary)]">
                    {user?.username}
                    {user?.role === "admin" && (
                      <span className="ml-1.5 rounded-full bg-[var(--color-accent-light)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-accent)]">
                        admin
                      </span>
                    )}
                  </span>
                </div>

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

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8 animate-fade-in">
        {children}
      </main>
    </div>
  );
}
