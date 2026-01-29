import { Train, Github, Twitter, Linkedin } from "lucide-react";
import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="bg-card border-t border-border py-12">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <Link to="/" className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl hero-gradient flex items-center justify-center">
                <Train className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-foreground">
                Pareto<span className="text-gradient">Route</span>
              </span>
            </Link>
            <p className="text-sm text-muted-foreground">
              AI-powered train route optimization for the perfect journey.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/" className="hover:text-foreground transition-colors">Features</Link></li>
              <li><a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a></li>
              <li><Link to="/docs" className="hover:text-foreground transition-colors">API</Link></li>
              <li><Link to="/docs" className="hover:text-foreground transition-colors">Documentation</Link></li>
              <li><Link to="/status" className="hover:text-foreground transition-colors">Status</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-foreground mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/benchmarks" className="hover:text-foreground transition-colors">About</Link></li>
              <li><a href="#" className="hover:text-foreground transition-colors">Blog</a></li>
              <li><a href="#" className="hover:text-foreground transition-colors">Careers</a></li>
              <li><Link to="/contact" className="hover:text-foreground transition-colors">Contact</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-foreground mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/privacy" className="hover:text-foreground transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-foreground transition-colors">Terms of Service</Link></li>
              <li><a href="#" className="hover:text-foreground transition-colors">Cookie Policy</a></li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground mb-4 md:mb-0">
            © 2024 ParetoRoute. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a href="#" className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <Twitter className="w-5 h-5 text-muted-foreground" />
            </a>
            <a href="#" className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <Github className="w-5 h-5 text-muted-foreground" />
            </a>
            <a href="#" className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <Linkedin className="w-5 h-5 text-muted-foreground" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
