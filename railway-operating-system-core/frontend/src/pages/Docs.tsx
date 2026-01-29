import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const Docs = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-8">API Documentation</h1>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Authentication</h2>
            <p className="mb-4">All API requests require an API key in the header:</p>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto">
              <code>X-API-Key: your-api-key-here</code>
            </pre>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Endpoints</h2>

            <div className="space-y-6">
              <div className="border rounded-lg p-6">
                <h3 className="text-xl font-medium mb-2">GET /api/routes</h3>
                <p className="mb-4">Search for routes between stations</p>
                <h4 className="font-medium mb-2">Parameters:</h4>
                <ul className="list-disc list-inside mb-4 space-y-1">
                  <li><code>origin</code> (string): Origin station code</li>
                  <li><code>destination</code> (string): Destination station code</li>
                  <li><code>date</code> (string): Travel date (YYYY-MM-DD)</li>
                  <li><code>max_transfers</code> (number): Maximum number of transfers (default: 3)</li>
                </ul>
                <h4 className="font-medium mb-2">Response:</h4>
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`{
  "routes": [
    {
      "id": "route-1",
      "origin": "STATION_A",
      "destination": "STATION_B",
      "departure_time": "08:00",
      "arrival_time": "10:30",
      "duration": "2h 30m",
      "transfers": 1,
      "trains": [...]
    }
  ]
}`}
                </pre>
              </div>

              <div className="border rounded-lg p-6">
                <h3 className="text-xl font-medium mb-2">POST /api/jobs</h3>
                <p className="mb-4">Enqueue a background job</p>
                <h4 className="font-medium mb-2">Body:</h4>
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`{
  "type": "route_export",
  "parameters": {
    "origin": "STATION_A",
    "destination": "STATION_B"
  }
}`}
                </pre>
              </div>

              <div className="border rounded-lg p-6">
                <h3 className="text-xl font-medium mb-2">GET /api/jobs/{'{job_id}'}</h3>
                <p className="mb-4">Get job status and results</p>
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Quick Start</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-medium mb-3">Postman Collection</h3>
                <p className="text-muted-foreground mb-4">
                  Import our Postman collection to quickly test all endpoints with pre-configured requests.
                </p>
                <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  Download Postman Collection
                </button>
              </div>
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-medium mb-3">SDK Downloads</h3>
                <p className="text-muted-foreground mb-4">
                  Official client libraries to integrate with our API in your preferred language.
                </p>
                <div className="space-y-2">
                  <button className="w-full px-4 py-2 border rounded-md hover:bg-muted">
                    Python SDK
                  </button>
                  <button className="w-full px-4 py-2 border rounded-md hover:bg-muted">
                    JavaScript SDK
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Error Handling</h2>
            <p className="mb-4">Standard HTTP status codes with JSON error responses:</p>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`{
  "error": "Invalid API key",
  "code": "AUTH_INVALID",
  "details": "The provided API key is not valid"
}`}
            </pre>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Docs;