import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Clock, Users, Zap } from "lucide-react";

const Benchmarks = () => {
  const benchmarks = [
    {
      metric: "Route Search Latency",
      p50: "45ms",
      p95: "120ms",
      p99: "250ms",
      description: "Time to find optimal routes between stations"
    },
    {
      metric: "Concurrent Users",
      p50: "10,000",
      p95: "25,000",
      p99: "50,000",
      description: "Simultaneous users supported"
    },
    {
      metric: "Route Accuracy",
      p50: "99.8%",
      p95: "99.9%",
      p99: "99.95%",
      description: "Routes match actual train schedules"
    },
    {
      metric: "API Uptime",
      p50: "99.9%",
      p95: "99.95%",
      p99: "99.99%",
      description: "Service availability (SLA)"
    }
  ];

  const caseStudies = [
    {
      company: "CityTransit App",
      industry: "Mobility",
      challenge: "Needed real-time route planning for 2M daily users",
      solution: "Integrated Railway OS API with custom mobile app",
      results: [
        "40% faster route searches",
        "95% user satisfaction increase",
        "2M+ routes calculated daily"
      ],
      logo: "🚇"
    },
    {
      company: "LogiCorp",
      industry: "Logistics",
      challenge: "Complex multi-modal freight routing optimization",
      solution: "Used advanced routing engine with custom constraints",
      results: [
        "25% cost reduction",
        "15% faster delivery times",
        "Real-time delay handling"
      ],
      logo: "🚛"
    },
    {
      company: "TravelCorp",
      industry: "Corporate Travel",
      challenge: "Booking system integration for employee travel",
      solution: "Webhook integration with existing booking platform",
      results: [
        "80% booking time reduction",
        "Zero integration errors",
        "Full audit trail"
      ],
      logo: "✈️"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">Performance Benchmarks</h1>
            <p className="text-xl text-muted-foreground">
              Industry-leading performance and reliability metrics
            </p>
          </div>

          <section className="mb-16">
            <h2 className="text-3xl font-bold mb-8">Key Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {benchmarks.map((benchmark, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="text-lg">{benchmark.metric}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">P50</span>
                        <span className="font-medium">{benchmark.p50}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">P95</span>
                        <span className="font-medium">{benchmark.p95}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">P99</span>
                        <span className="font-medium">{benchmark.p99}</span>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-4">{benchmark.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section className="mb-16">
            <h2 className="text-3xl font-bold mb-8">Case Studies</h2>
            <div className="space-y-8">
              {caseStudies.map((study, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <div className="text-3xl">{study.logo}</div>
                      <div>
                        <CardTitle className="text-xl">{study.company}</CardTitle>
                        <Badge variant="outline">{study.industry}</Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="font-medium mb-2">Challenge</h3>
                        <p className="text-muted-foreground mb-4">{study.challenge}</p>
                        <h3 className="font-medium mb-2">Solution</h3>
                        <p className="text-muted-foreground">{study.solution}</p>
                      </div>
                      <div>
                        <h3 className="font-medium mb-2">Results</h3>
                        <ul className="space-y-2">
                          {study.results.map((result, idx) => (
                            <li key={idx} className="flex items-center gap-2">
                              <div className="w-2 h-2 bg-green-500 rounded-full" />
                              <span className="text-sm">{result}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section className="mb-16">
            <h2 className="text-3xl font-bold mb-8">Architecture Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-500" />
                    <CardTitle className="text-lg">High Performance</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Optimized algorithms and caching ensure sub-100ms response times
                    even for complex route calculations.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-500" />
                    <CardTitle className="text-lg">Scalable</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Multi-tenant architecture supports thousands of concurrent users
                    with automatic scaling.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-green-500" />
                    <CardTitle className="text-lg">Reliable</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    99.9% uptime SLA with comprehensive monitoring and
                    automatic failover systems.
                  </p>
                </CardContent>
              </Card>
            </div>
          </section>

          <section className="text-center">
            <Card>
              <CardContent className="pt-6">
                <h2 className="text-2xl font-bold mb-4">Ready to Get Started?</h2>
                <p className="text-muted-foreground mb-6">
                  Join thousands of developers building the future of transportation.
                </p>
                <div className="flex gap-4 justify-center">
                  <button className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                    Start Free Trial
                  </button>
                  <button className="px-6 py-2 border rounded-md hover:bg-muted">
                    View Documentation
                  </button>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Benchmarks;