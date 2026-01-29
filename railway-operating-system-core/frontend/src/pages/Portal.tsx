import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Key, CreditCard, BarChart3, Download } from "lucide-react";

const Portal = () => {
  const [apiKey, setApiKey] = useState("demo-api-key-12345");
  const [usage, setUsage] = useState({
    requests: 15420,
    jobs: 45,
    storage: "2.3 GB",
    limit: 100000
  });

  const [billing, setBilling] = useState([
    { date: "2024-01-01", amount: 150.00, status: "Paid" },
    { date: "2023-12-01", amount: 150.00, status: "Paid" },
  ]);

  const regenerateApiKey = () => {
    setApiKey(`new-key-${Date.now()}`);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-8">Customer Portal</h1>

          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="api">API Keys</TabsTrigger>
              <TabsTrigger value="billing">Billing</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">API Requests</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{usage.requests.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      {((usage.requests / usage.limit) * 100).toFixed(1)}% of limit
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Background Jobs</CardTitle>
                    <Download className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{usage.jobs}</div>
                    <p className="text-xs text-muted-foreground">This month</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{usage.storage}</div>
                    <p className="text-xs text-muted-foreground">Total stored</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-4">
                    <Button>View API Documentation</Button>
                    <Button variant="outline">Download SDK</Button>
                    <Button variant="outline">Create Support Ticket</Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="api" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>API Key Management</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Key className="h-5 w-5" />
                    <div className="flex-1">
                      <p className="font-medium">Current API Key</p>
                      <p className="text-sm text-muted-foreground font-mono">{apiKey}</p>
                    </div>
                    <Button variant="outline" onClick={regenerateApiKey}>
                      Regenerate
                    </Button>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm">
                      <strong>Warning:</strong> Regenerating your API key will invalidate the current key.
                      Update your applications immediately.
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Webhook Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Webhook URL</label>
                    <Input placeholder="https://your-app.com/webhooks" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Secret</label>
                    <Input type="password" placeholder="Webhook secret" />
                  </div>
                  <Button>Save Webhook Settings</Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="billing" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Billing History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {billing.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <p className="font-medium">{item.date}</p>
                          <p className="text-sm text-muted-foreground">Monthly subscription</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">${item.amount}</p>
                          <Badge variant={item.status === "Paid" ? "default" : "secondary"}>
                            {item.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Payment Method</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">No payment method on file</p>
                  <Button>Add Payment Method</Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="usage" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h3 className="font-medium">Current Plan</h3>
                        <p className="text-2xl font-bold">Premium</p>
                        <p className="text-sm text-muted-foreground">$150/month</p>
                      </div>
                      <div>
                        <h3 className="font-medium">Next Billing</h3>
                        <p className="text-2xl font-bold">Feb 1, 2024</p>
                        <p className="text-sm text-muted-foreground">30 days remaining</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Portal;