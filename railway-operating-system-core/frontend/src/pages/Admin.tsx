import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

const Admin = () => {
  const [tenants, setTenants] = useState([
    { id: 1, name: "Demo Corp", apiKey: "demo-key-123", plan: "Premium", status: "Active" },
    { id: 2, name: "Test Inc", apiKey: "test-key-456", plan: "Basic", status: "Active" },
  ]);

  const [usage, setUsage] = useState([
    { tenant: "Demo Corp", requests: 15420, jobs: 45, storage: "2.3 GB" },
    { tenant: "Test Inc", requests: 2340, jobs: 12, storage: "0.8 GB" },
  ]);

  const [newTenant, setNewTenant] = useState({ name: "", plan: "Basic" });

  const handleCreateTenant = () => {
    const tenant = {
      id: tenants.length + 1,
      name: newTenant.name,
      apiKey: `key-${Date.now()}`,
      plan: newTenant.plan,
      status: "Active"
    };
    setTenants([...tenants, tenant]);
    setNewTenant({ name: "", plan: "Basic" });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-8">Admin Console</h1>

          <Tabs defaultValue="tenants" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="tenants">Tenants</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
              <TabsTrigger value="jobs">Jobs</TabsTrigger>
              <TabsTrigger value="system">System</TabsTrigger>
            </TabsList>

            <TabsContent value="tenants" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Create New Tenant</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      placeholder="Tenant Name"
                      value={newTenant.name}
                      onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                    />
                    <select
                      className="px-3 py-2 border rounded-md"
                      value={newTenant.plan}
                      onChange={(e) => setNewTenant({ ...newTenant, plan: e.target.value })}
                    >
                      <option value="Sandbox">Sandbox</option>
                      <option value="Basic">Basic</option>
                      <option value="Premium">Premium</option>
                    </select>
                  </div>
                  <Button onClick={handleCreateTenant}>Create Tenant</Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Existing Tenants</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {tenants.map((tenant) => (
                      <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">{tenant.name}</h3>
                          <p className="text-sm text-muted-foreground">API Key: {tenant.apiKey}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={tenant.plan === "Premium" ? "default" : "secondary"}>
                            {tenant.plan}
                          </Badge>
                          <Badge variant="outline">{tenant.status}</Badge>
                          <Button variant="outline" size="sm">Edit</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="usage" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Usage Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {usage.map((item, index) => (
                      <div key={index} className="grid grid-cols-4 gap-4 p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">{item.tenant}</h3>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Requests</p>
                          <p className="font-medium">{item.requests.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Jobs</p>
                          <p className="font-medium">{item.jobs}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Storage</p>
                          <p className="font-medium">{item.storage}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="jobs" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Background Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">Job monitoring and management interface</p>
                  {/* Job management UI would go here */}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="system" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Health</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-medium">Database</h3>
                      <Badge variant="outline" className="mt-2">Healthy</Badge>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-medium">Cache</h3>
                      <Badge variant="outline" className="mt-2">Healthy</Badge>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-medium">Workers</h3>
                      <Badge variant="outline" className="mt-2">3/3 Running</Badge>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-medium">API</h3>
                      <Badge variant="outline" className="mt-2">99.9% Uptime</Badge>
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

export default Admin;