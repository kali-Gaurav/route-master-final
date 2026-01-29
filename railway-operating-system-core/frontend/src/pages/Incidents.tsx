import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, Clock, MapPin } from "lucide-react";

const Incidents = () => {
  const [incidents] = useState([
    {
      id: 1,
      title: "Signal Failure at Central Station",
      status: "Active",
      severity: "High",
      affectedRoutes: ["Route A", "Route B", "Route C"],
      description: "Signal system malfunction causing delays on multiple lines",
      startTime: "2024-01-28 14:30",
      estimatedResolution: "2024-01-28 16:00",
      updates: [
        "14:30 - Signal failure detected",
        "14:45 - Engineers dispatched",
        "15:00 - Alternative routing activated"
      ]
    },
    {
      id: 2,
      title: "Track Maintenance - Line 2",
      status: "Resolved",
      severity: "Medium",
      affectedRoutes: ["Route D"],
      description: "Scheduled maintenance completed successfully",
      startTime: "2024-01-28 08:00",
      estimatedResolution: "2024-01-28 12:00",
      updates: [
        "08:00 - Maintenance began",
        "12:00 - Maintenance completed, service restored"
      ]
    }
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Active":
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case "Resolved":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "High":
        return "destructive";
      case "Medium":
        return "default";
      case "Low":
        return "secondary";
      default:
        return "outline";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-8">Incident Dashboard</h1>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Incidents</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1</div>
                <p className="text-xs text-muted-foreground">Currently affecting service</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Resolved Today</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3</div>
                <p className="text-xs text-muted-foreground">Incidents resolved</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Status</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">Healthy</div>
                <p className="text-xs text-muted-foreground">All systems operational</p>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            {incidents.map((incident) => (
              <Card key={incident.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(incident.status)}
                      <div>
                        <CardTitle className="text-xl">{incident.title}</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">{incident.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getSeverityColor(incident.severity)}>
                        {incident.severity}
                      </Badge>
                      <Badge variant={incident.status === "Resolved" ? "default" : "destructive"}>
                        {incident.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <h3 className="font-medium mb-2">Affected Routes</h3>
                      <div className="flex flex-wrap gap-2">
                        {incident.affectedRoutes.map((route, index) => (
                          <Badge key={index} variant="outline">
                            <MapPin className="h-3 w-3 mr-1" />
                            {route}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">Timeline</h3>
                      <div className="space-y-1 text-sm">
                        <p><strong>Started:</strong> {incident.startTime}</p>
                        {incident.status === "Active" ? (
                          <p><strong>Estimated Resolution:</strong> {incident.estimatedResolution}</p>
                        ) : (
                          <p><strong>Resolved:</strong> {incident.estimatedResolution}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-medium mb-2">Updates</h3>
                    <div className="space-y-2">
                      {incident.updates.map((update, index) => (
                        <div key={index} className="flex items-start gap-2 text-sm">
                          <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                          <p>{update}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Subscribe to Updates</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                Get notified about service incidents and maintenance windows via email or webhook.
              </p>
              <div className="flex gap-4">
                <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  Subscribe to Email Alerts
                </button>
                <button className="px-4 py-2 border rounded-md hover:bg-muted">
                  Configure Webhook
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Incidents;