import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, AlertTriangle, XCircle, Clock, Activity } from "lucide-react";

const Status = () => {
  const services = [
    {
      name: "API Gateway",
      status: "operational",
      uptime: "99.9%",
      responseTime: "45ms"
    },
    {
      name: "Route Service",
      status: "operational",
      uptime: "99.8%",
      responseTime: "120ms"
    },
    {
      name: "Data Service",
      status: "operational",
      uptime: "99.9%",
      responseTime: "35ms"
    },
    {
      name: "Auth Service",
      status: "operational",
      uptime: "99.9%",
      responseTime: "25ms"
    },
    {
      name: "Worker Service",
      status: "degraded",
      uptime: "98.5%",
      responseTime: "250ms"
    },
    {
      name: "Cache (Redis)",
      status: "operational",
      uptime: "99.9%",
      responseTime: "5ms"
    }
  ];

  const incidents = [
    {
      id: 1,
      title: "Worker Service Performance Degradation",
      status: "investigating",
      started: "2024-01-28 10:30 UTC",
      description: "We're experiencing slower response times in the job processing service. Our team is investigating."
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "operational":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case "outage":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "operational":
        return <Badge variant="default" className="bg-green-500">Operational</Badge>;
      case "degraded":
        return <Badge variant="secondary" className="bg-yellow-500">Degraded</Badge>;
      case "outage":
        return <Badge variant="destructive">Outage</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const overallStatus = services.every(s => s.status === "operational") ? "operational" :
                       services.some(s => s.status === "outage") ? "outage" : "degraded";

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-4 mb-4">
              {getStatusIcon(overallStatus)}
              <h1 className="text-4xl font-bold">System Status</h1>
            </div>
            <p className="text-xl text-muted-foreground">
              Current status of Railway OS services
            </p>
          </div>

          {/* Overall Status */}
          <Card className="mb-8">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusIcon(overallStatus)}
                  <div>
                    <h2 className="text-2xl font-bold">All Systems Operational</h2>
                    <p className="text-muted-foreground">
                      Railway OS is running normally. View detailed status below.
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Last updated</p>
                  <p className="font-medium">2 minutes ago</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Service Status */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6">Service Status</h2>
            <div className="grid gap-4">
              {services.map((service, index) => (
                <Card key={index}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(service.status)}
                        <div>
                          <h3 className="font-medium">{service.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {service.uptime} uptime • {service.responseTime} avg response
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(service.status)}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Active Incidents */}
          {incidents.length > 0 && (
            <div className="mb-12">
              <h2 className="text-2xl font-bold mb-6">Active Incidents</h2>
              <div className="space-y-4">
                {incidents.map((incident) => (
                  <Card key={incident.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{incident.title}</CardTitle>
                        <Badge variant="secondary">Investigating</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground mb-4">{incident.description}</p>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          <span>Started: {incident.started}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Activity className="h-4 w-4" />
                          <span>Updated: 5 minutes ago</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Uptime History */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6">90-Day Uptime</h2>
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">99.9%</div>
                    <p className="text-muted-foreground">Overall Uptime</p>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">99.8%</div>
                    <p className="text-muted-foreground">API Uptime</p>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">99.9%</div>
                    <p className="text-muted-foreground">Data Service Uptime</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Subscribe to Updates */}
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-4">Stay Informed</h2>
                <p className="text-muted-foreground mb-6">
                  Get notified about service incidents and maintenance windows.
                </p>
                <div className="flex gap-4 justify-center">
                  <button className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                    Subscribe to Updates
                  </button>
                  <button className="px-6 py-2 border rounded-md hover:bg-muted">
                    View Incident History
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Status;