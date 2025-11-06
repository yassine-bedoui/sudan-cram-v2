import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, TrendingUp, MapPin, Users } from 'lucide-react';
import { conflictPronenessAPI } from '../services/api';

interface DashboardData {
  summary: {
    conflict_events: number;
    states_analyzed: number;
    risk_assessments: number;
    data_confidence: number;
  };
  quick_insights: {
    highest_risk_state: string;
    active_alerts: number;
    alert_breakdown: {
      high: number;
      very_high: number;
      extreme: number;
    };
    trend: {
      direction: string;
      percentage: number;
    };
  };
  risk_distribution: {
    climate: Record<string, number>;
    conflict: Record<string, number>;
  };
  metrics: {
    total_events: number;
    total_fatalities: number;
    avg_conflict_proneness: number;
    avg_climate_risk: number;
  };
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const response = await conflictPronenessAPI.getDashboard();
        setData(response);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-screen text-red-600">Error: {error}</div>;
  }

  if (!data) {
    return <div className="flex items-center justify-center h-screen">No data available</div>;
  }

  const conflictData = Object.entries(data.risk_distribution.conflict).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'];

  return (
    <div className="w-full bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">CRAM Dashboard</h1>
          <p className="text-gray-400">Conflict Risk Assessment & Monitoring System</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Conflict Events</p>
                <p className="text-3xl font-bold">{data.summary.conflict_events}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">States Analyzed</p>
                <p className="text-3xl font-bold">{data.summary.states_analyzed}</p>
              </div>
              <MapPin className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Alerts</p>
                <p className="text-3xl font-bold">{data.quick_insights.active_alerts}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Data Confidence</p>
                <p className="text-3xl font-bold">{data.summary.data_confidence}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>
        </div>

        {/* Risk Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Highest Risk State</h3>
            <p className="text-2xl font-bold text-red-400">{data.quick_insights.highest_risk_state}</p>
            <p className="text-gray-400 mt-2">Requires immediate attention</p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Alert Breakdown</h3>
            <div className="space-y-2">
              <p className="flex justify-between"><span className="text-gray-400">Extreme:</span> <span className="text-red-400 font-bold">{data.quick_insights.alert_breakdown.extreme}</span></p>
              <p className="flex justify-between"><span className="text-gray-400">Very High:</span> <span className="text-orange-400 font-bold">{data.quick_insights.alert_breakdown.very_high}</span></p>
              <p className="flex justify-between"><span className="text-gray-400">High:</span> <span className="text-yellow-400 font-bold">{data.quick_insights.alert_breakdown.high}</span></p>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Trend</h3>
            <p className="text-2xl font-bold text-yellow-400">{data.quick_insights.trend.percentage}% <span className="text-sm">{data.quick_insights.trend.direction}</span></p>
            <p className="text-gray-400 mt-2">30-day trend</p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Conflict Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={conflictData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}`} outerRadius={80} fill="#8884d8" dataKey="value">
                  {conflictData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Key Metrics</h3>
            <div className="space-y-4">
              <div className="flex justify-between pb-3 border-b border-gray-700">
                <span className="text-gray-400">Total Events</span>
                <span className="font-bold">{data.metrics.total_events}</span>
              </div>
              <div className="flex justify-between pb-3 border-b border-gray-700">
                <span className="text-gray-400">Total Fatalities</span>
                <span className="font-bold text-red-400">{data.metrics.total_fatalities}</span>
              </div>
              <div className="flex justify-between pb-3 border-b border-gray-700">
                <span className="text-gray-400">Avg Conflict Proneness</span>
                <span className="font-bold">{data.metrics.avg_conflict_proneness.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Avg Climate Risk</span>
                <span className="font-bold">{data.metrics.avg_climate_risk.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
