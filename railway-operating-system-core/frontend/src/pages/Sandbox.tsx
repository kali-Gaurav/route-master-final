import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Play, Code, Book, Key } from "lucide-react";

const Sandbox = () => {
  const [apiKey] = useState("demo-api-key-12345");
  const [selectedEndpoint, setSelectedEndpoint] = useState("routes");
  const [requestData, setRequestData] = useState({
    origin: "STATION_A",
    destination: "STATION_B",
    date: "2024-01-28"
  });
  const [response, setResponse] = useState("");

  const endpoints = [
    {
      id: "routes",
      name: "GET /api/routes",
      description: "Search for routes between stations",
      params: ["origin", "destination", "date", "max_transfers"]
    },
    {
      id: "jobs",
      name: "POST /api/jobs",
      description: "Enqueue a background job",
      params: ["type", "parameters"]
    },
    {
      id: "stations",
      name: "GET /api/stations",
      description: "Get station information",
      params: ["query", "limit"]
    }
  ];

  const sampleData = {
    routes: {
      origin: "STATION_A",
      destination: "STATION_B",
      date: "2024-01-28",
      max_transfers: 2
    },
    jobs: {
      type: "route_export",
      parameters: {
        origin: "STATION_A",
        destination: "STATION_B"
      }
    },
    stations: {
      query: "central",
      limit: 10
    }
  };

  const handleTestRequest = async () => {
    const endpoint = endpoints.find(e => e.id === selectedEndpoint);
    if (!endpoint) return;

    const url = `https://api.railway-os.com/${endpoint.id}`;
    const headers = {
      "X-API-Key": apiKey,
      "Content-Type": "application/json"
    };

    let options: RequestInit = { headers };

    if (endpoint.name.includes("POST")) {
      options.method = "POST";
      options.body = JSON.stringify(sampleData[selectedEndpoint as keyof typeof sampleData], null, 2);
    } else {
      const params = new URLSearchParams();
      const data = sampleData[selectedEndpoint as keyof typeof sampleData] as any;
      Object.entries(data).forEach(([key, value]) => {
        params.append(key, value.toString());
      });
      options.method = "GET";
    }

    setResponse(`// Making request to ${endpoint.name}\n// ${endpoint.description}\n\n${JSON.stringify({
      url: endpoint.name.includes("POST") ? url : `${url}?${new URLSearchParams(Object.entries(sampleData[selectedEndpoint as keyof typeof sampleData] as any).map(([k, v]) => [k, v.toString()]))}`,
      method: options.method,
      headers,
      body: options.body
    }, null, 2)}`);

    // Simulate API response
    setTimeout(() => {
      const mockResponse = selectedEndpoint === "routes" ? {
        routes: [
          {
            id: "route-1",
            origin: "STATION_A",
            destination: "STATION_B",
            departure_time: "08:00",
            arrival_time: "10:30",
            duration: "2h 30m",
            transfers: 1,
            trains: ["Train A", "Train B"]
          }
        ]
      } : selectedEndpoint === "jobs" ? {
        job_id: "job-123",
        status: "queued",
        created_at: "2024-01-28T10:00:00Z"
      } : {
        stations: [
          { code: "STATION_A", name: "Central Station", city: "Metropolis" },
          { code: "STATION_B", name: "North Station", city: "Metropolis" }
        ]
      };

      setResponse(prev => prev + `\n\n// Response:\n${JSON.stringify(mockResponse, null, 2)}`);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4">Developer Sandbox</h1>
            <p className="text-xl text-muted-foreground">
              Test our APIs with sample data and your demo API key
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    Demo API Key
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-2">Use this key for testing:</p>
                  <div className="bg-muted p-3 rounded font-mono text-sm break-all">
                    {apiKey}
                  </div>
                  <Badge variant="outline" className="mt-2">Rate Limit: 100 req/hour</Badge>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Book className="h-5 w-5" />
                    Quick Start
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h4 className="font-medium">1. Choose an endpoint</h4>
                    <p className="text-sm text-muted-foreground">Select from the available API endpoints</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">2. Test the request</h4>
                    <p className="text-sm text-muted-foreground">Click "Test Request" to see the API in action</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">3. View response</h4>
                    <p className="text-sm text-muted-foreground">Check the response format and data</p>
                  </div>
                  <Button className="w-full" variant="outline">
                    <Book className="mr-2 h-4 w-4" />
                    Full Documentation
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-2">
              <Tabs value={selectedEndpoint} onValueChange={setSelectedEndpoint}>
                <TabsList className="grid w-full grid-cols-3">
                  {endpoints.map((endpoint) => (
                    <TabsTrigger key={endpoint.id} value={endpoint.id}>
                      {endpoint.name}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {endpoints.map((endpoint) => (
                  <TabsContent key={endpoint.id} value={endpoint.id} className="space-y-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>{endpoint.name}</CardTitle>
                        <p className="text-muted-foreground">{endpoint.description}</p>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium mb-2">Parameters</h4>
                            <div className="grid grid-cols-2 gap-4">
                              {endpoint.params.map((param) => (
                                <div key={param} className="space-y-1">
                                  <label className="text-sm font-medium">{param}</label>
                                  <Input
                                    placeholder={`Enter ${param}`}
                                    value={(sampleData[endpoint.id as keyof typeof sampleData] as any)[param] || ""}
                                    onChange={(e) => {
                                      const newData = { ...sampleData[endpoint.id as keyof typeof sampleData] as any };
                                      newData[param] = e.target.value;
                                      setRequestData(newData);
                                    }}
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                          <Button onClick={handleTestRequest} className="w-full">
                            <Play className="mr-2 h-4 w-4" />
                            Test Request
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Response</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm whitespace-pre-wrap">
                          {response || "// Click 'Test Request' to see the API response"}
                        </pre>
                      </CardContent>
                    </Card>
                  </TabsContent>
                ))}
              </Tabs>
            </div>
          </div>

          <Card className="mt-8">
            <CardContent className="pt-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-4">Ready for Production?</h2>
                <p className="text-muted-foreground mb-6">
                  Get your own API key and start building with real data.
                </p>
                <div className="flex gap-4 justify-center">
                  <Button>Sign Up for Free</Button>
                  <Button variant="outline">Contact Sales</Button>
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

export default Sandbox;