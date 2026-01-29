import { Search, Route, CheckCircle } from "lucide-react";

export function HowItWorksSection() {
  const steps = [
    {
      icon: Search,
      title: "Search Routes",
      description: "Enter your origin and destination stations, along with travel date and preferences."
    },
    {
      icon: Route,
      title: "Get Optimized Routes",
      description: "Our AI finds the best routes balancing time, cost, transfers, and seat availability."
    },
    {
      icon: CheckCircle,
      title: "Book & Travel",
      description: "Choose your preferred route and proceed with booking through integrated partners."
    }
  ];

  return (
    <section className="py-20 bg-secondary/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            How It Works
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Finding the perfect train route is now as simple as three steps.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {steps.map((step, idx) => (
            <div key={step.title} className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <step.icon className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
              <p className="text-muted-foreground">{step.description}</p>
              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-primary/20 transform -translate-x-1/2" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}