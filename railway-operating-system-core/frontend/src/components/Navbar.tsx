import { Train, Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/docs", label: "Docs" },
    { href: "/sandbox", label: "Sandbox" },
    { href: "/benchmarks", label: "Benchmarks" },
    { href: "/status", label: "Status" },
    { href: "/portal", label: "Portal" },
    { href: "/admin", label: "Admin" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl hero-gradient flex items-center justify-center">
              <Train className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">
              Pareto<span className="text-gradient">Route</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "text-muted-foreground hover:text-foreground transition-colors",
                  location.pathname === item.href && "text-foreground font-medium"
                )}
              >
                {item.label}
              </Link>
            ))}
            <Link to="/onboarding">
              <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity">
                Get Started
              </button>
            </Link>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? (
              <X className="w-6 h-6 text-foreground" />
            ) : (
              <Menu className="w-6 h-6 text-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-border bg-background animate-fade-in">
          <div className="container mx-auto px-4 py-4 space-y-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "block py-2 text-foreground",
                  location.pathname === item.href && "font-medium"
                )}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <Link to="/onboarding" onClick={() => setIsMenuOpen(false)}>
              <button className="w-full px-4 py-3 rounded-lg bg-primary text-primary-foreground font-medium">
                Get Started
              </button>
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
