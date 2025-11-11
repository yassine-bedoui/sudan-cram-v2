import Link from 'next/link'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Sudan CRAM</h1>
          <div className="flex gap-4">
            <Link href="/sign-in" className="text-gray-600 hover:text-gray-900">
              Sign In
            </Link>
            <Link 
              href="/sign-up" 
              className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
	  <section className="container mx-auto px-4 py-20">
	    <div className="max-w-4xl mx-auto text-center">
		  <h1 className="text-5xl font-bold text-gray-900 mb-6">
		    Real-Time Conflict Monitoring for Sudan
		  </h1>
		  <p className="text-xl text-gray-600 mb-8">
			Get early warnings on conflict risks and climate threats to protect your people and make data-driven decisions faster.
		  </p>
		  <div className="flex gap-4 justify-center flex-wrap">
		    <Link 
			  href="/sign-up"
			  className="bg-orange-600 text-white px-8 py-3 rounded-lg text-lg hover:bg-orange-700"
		    >
			  Start Free Trial
		    </Link>
		  </div>
	    </div>
	  </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-4">⚡</div>
              <h3 className="text-xl font-bold mb-3">Real-Time Updates</h3>
              <p className="text-gray-600">
                15-minute update cycles from GDELT's 100,000+ global news sources
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-4">🌍</div>
              <h3 className="text-xl font-bold mb-3">Climate Correlation</h3>
              <p className="text-gray-600">
                Analyze drought patterns and their impact on conflict risk
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-4">🔔</div>
              <h3 className="text-xl font-bold mb-3">Custom Alerts</h3>
              <p className="text-gray-600">
                SMS and email notifications for your specific locations
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-8">Built for Humanitarian Organizations</h2>
            <div className="bg-orange-50 border-l-4 border-orange-600 p-6 mb-8">
              <p className="text-lg text-gray-700 italic">
                "Sudan CRAM detected the Wad Madani escalation 72 hours before it appeared in mainstream media. 
                This early warning gave us critical time to adjust field operations."
              </p>
              <p className="text-sm text-gray-600 mt-4">— Humanitarian Partner (Beta Tester)</p>
            </div>
            <div className="grid grid-cols-3 gap-8 mt-12">
              <div>
                <p className="text-4xl font-bold text-orange-600">15min</p>
                <p className="text-gray-600 mt-2">Update Cycle</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-orange-600">100K+</p>
                <p className="text-gray-600 mt-2">News Sources</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-orange-600">24/7</p>
                <p className="text-gray-600 mt-2">Monitoring</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Simple Pricing</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Tier */}
            <div className="bg-white p-8 rounded-lg border">
              <h3 className="text-xl font-bold mb-2">Free</h3>
              <p className="text-gray-600 mb-4">Public Dashboard</p>
              <p className="text-3xl font-bold mb-6">$0<span className="text-sm text-gray-500">/month</span></p>
              <ul className="space-y-2 mb-6 text-sm">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>View-only access</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>24-hour data delay</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Basic conflict data</span>
                </li>
              </ul>
              <Link href="/dashboard" className="block text-center border border-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-50">
                View Dashboard
              </Link>
            </div>

            {/* Pro Tier */}
            <div className="bg-white p-8 rounded-lg border-2 border-orange-600 relative shadow-lg transform scale-105">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-orange-600 text-white px-4 py-1 rounded-full text-sm">
                Popular
              </div>
              <h3 className="text-xl font-bold mb-2">Pro</h3>
              <p className="text-gray-600 mb-4">For Organizations</p>
              <p className="text-3xl font-bold mb-6">$299<span className="text-sm text-gray-500">/month</span></p>
              <ul className="space-y-2 mb-6 text-sm">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Real-time data access</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>API access</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Custom alerts (SMS/Email)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>5 monitored regions</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Priority support</span>
                </li>
              </ul>
              <Link href="/sign-up" className="block text-center bg-orange-600 text-white px-6 py-2 rounded hover:bg-orange-700">
                Start Free Trial
              </Link>
            </div>

            {/* Enterprise Tier */}
            <div className="bg-white p-8 rounded-lg border">
              <h3 className="text-xl font-bold mb-2">Enterprise</h3>
              <p className="text-gray-600 mb-4">Custom Solution</p>
              <p className="text-3xl font-bold mb-6">Custom</p>
              <ul className="space-y-2 mb-6 text-sm">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>White-label branding</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Dedicated support</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Custom integrations</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Unlimited regions</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>SLA guarantee</span>
                </li>
              </ul>
              <a href="mailto:hello@sudancram.com" className="block text-center border border-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-50">
                Contact Sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center bg-orange-600 text-white p-12 rounded-lg">
            <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
            <p className="text-xl mb-8">Join humanitarian organizations monitoring Sudan with CRAM</p>
            <Link 
              href="/sign-up"
              className="inline-block bg-white text-orange-600 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-600 text-sm">© 2025 Sudan CRAM. All rights reserved.</p>
            <div className="flex gap-6">
              <a href="mailto:hello@sudancram.com" className="text-gray-600 hover:text-gray-900 text-sm">Contact</a>
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 text-sm">Dashboard</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
