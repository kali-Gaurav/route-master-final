import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function PricingSection() {
  const plans = [
    {
      name: "Sandbox",
      price: "Free",
      description: "Perfect for testing and development",
      features: [
        "100 requests/hour",
        "Demo dataset access",
        "Basic API endpoints",
        "Community support",
        "Rate limiting"
      ],
      cta: "Get Started",
      popular: false
    },
    {
      name: "Basic",
      price: "$99",
      period: "month",
      description: "Great for small applications",
      features: [
        "1,000 requests/hour",
        "Full dataset access",
        "All API endpoints",
        "Email support",
        "Webhook notifications",
        "Basic analytics"
      ],
      cta: "Start Free Trial",
      popular: false
    },
    {
      name: "Premium",
      price: "$299",
      period: "month",
      description: "For high-traffic applications",
      features: [
        "10,000 requests/hour",
        "Priority support",
        "Advanced analytics",
        "Custom integrations",
        "SLA guarantee",
        "Dedicated account manager"
      ],
      cta: "Contact Sales",
      popular: true
    }
  ];

  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your needs. All plans include access to our comprehensive railway dataset.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <Card key={plan.name} className={`relative ${plan.popular ? 'border-primary shadow-lg' : ''}`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}
              <CardHeader className="text-center">
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="mt-4">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period && <span className="text-muted-foreground">/{plan.period}</span>}
                </div>
                <p className="text-muted-foreground mt-2">{plan.description}</p>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className={`w-full ${plan.popular ? '' : 'variant-outline'}`}>
                  {plan.cta}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center mt-12">
          <p className="text-muted-foreground">
            All plans include 99.9% uptime SLA and enterprise-grade security.
            <br />
            Need a custom plan? <a href="/contact" className="text-primary hover:underline">Contact us</a>
          </p>
        </div>
      </div>
    </section>
  );
}