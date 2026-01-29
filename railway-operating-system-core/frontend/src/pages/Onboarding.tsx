import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, ArrowRight, Key, Book, Play } from "lucide-react";

const Onboarding = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    companyName: "",
    email: "",
    useCase: "",
    apiKey: ""
  });

  const steps = [
    {
      title: "Welcome",
      description: "Get started with Railway Operating System",
      content: (
        <div className="text-center space-y-6">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
            <Play className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-2">Welcome to Railway OS</h2>
            <p className="text-muted-foreground">
              Let's get you set up with our route planning platform. This will take just a few minutes.
            </p>
          </div>
          <Button onClick={() => setCurrentStep(1)} className="w-full">
            Get Started
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      )
    },
    {
      title: "Company Details",
      description: "Tell us about your organization",
      content: (
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Company Name</label>
            <Input
              placeholder="Enter your company name"
              value={formData.companyName}
              onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Email Address</label>
            <Input
              type="email"
              placeholder="your@email.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Use Case</label>
            <select
              className="w-full px-3 py-2 border rounded-md"
              value={formData.useCase}
              onChange={(e) => setFormData({ ...formData, useCase: e.target.value })}
            >
              <option value="">Select your use case</option>
              <option value="travel_app">Travel/Mobility App</option>
              <option value="logistics">Logistics & Transportation</option>
              <option value="corporate">Corporate Travel</option>
              <option value="research">Research & Analytics</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="flex gap-4">
            <Button variant="outline" onClick={() => setCurrentStep(0)}>Back</Button>
            <Button
              onClick={() => setCurrentStep(2)}
              disabled={!formData.companyName || !formData.email || !formData.useCase}
              className="flex-1"
            >
              Continue
            </Button>
          </div>
        </div>
      )
    },
    {
      title: "API Setup",
      description: "Generate your API key",
      content: (
        <div className="space-y-6">
          <div className="p-6 bg-muted rounded-lg">
            <div className="flex items-center gap-3 mb-4">
              <Key className="h-5 w-5" />
              <h3 className="font-medium">Your API Key</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              This is your unique API key for accessing the Railway OS platform.
              Keep it secure and don't share it publicly.
            </p>
            <div className="bg-background p-3 rounded border font-mono text-sm">
              demo-api-key-{Date.now()}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium">Next Steps</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Review API Documentation</p>
                  <p className="text-sm text-muted-foreground">Learn about available endpoints and parameters</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Try the Sandbox</p>
                  <p className="text-sm text-muted-foreground">Test with our demo dataset and API key</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Upload Your Dataset</p>
                  <p className="text-sm text-muted-foreground">Provide your railway network data for custom routing</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <Button variant="outline" onClick={() => setCurrentStep(1)}>Back</Button>
            <Button onClick={() => setCurrentStep(3)} className="flex-1">
              Complete Setup
            </Button>
          </div>
        </div>
      )
    },
    {
      title: "Complete",
      description: "You're all set!",
      content: (
        <div className="text-center space-y-6">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-2">Setup Complete!</h2>
            <p className="text-muted-foreground">
              Welcome to Railway OS. Your account is ready and you can start building.
            </p>
          </div>
          <div className="space-y-4">
            <Button className="w-full">
              <Book className="mr-2 h-4 w-4" />
              View Documentation
            </Button>
            <Button variant="outline" className="w-full">
              <Play className="mr-2 h-4 w-4" />
              Try Sandbox
            </Button>
          </div>
        </div>
      )
    }
  ];

  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-4">Get Started</h1>
            <Progress value={progress} className="w-full" />
            <p className="text-sm text-muted-foreground mt-2">
              Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{steps[currentStep].title}</CardTitle>
              <p className="text-muted-foreground">{steps[currentStep].description}</p>
            </CardHeader>
            <CardContent>
              {steps[currentStep].content}
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Onboarding;